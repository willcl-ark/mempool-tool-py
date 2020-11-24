import logging
from collections import OrderedDict

import attr
from consensus import COIN, HALVING_INTERVAL

COINBASE_WEIGHT = 4000
COINBASE_SIGOPS = 400


logger = logging.getLogger(__name__)


@attr.s
class Block(object):
    pick_fields = [
        "hash",
        "size",
        "weight",
        "height",
        "version",
        "tx",
        "previousblockhash",
        "fee",
    ]

    height = attr.ib(type=int)
    version = attr.ib(type=int)
    tx = attr.ib(type=OrderedDict)
    previousblockhash = attr.ib(type=hex)
    hash = attr.ib(type=hex, default=64 * 0)
    size = attr.ib(type=int, default=0)
    weight = attr.ib(type=int, default=COINBASE_WEIGHT)
    fee = attr.ib(type=int, default=0)
    sigopscost = attr.ib(type=int, default=COINBASE_SIGOPS)
    template = attr.ib(type=bool, default=True)
    tip_offset = attr.ib(type=str, default="")

    @classmethod
    def from_getblock(cls, d, tip_offset=""):
        df = {k: v for k, v in d.items() if k in Block.pick_fields}
        return cls(tip_offset=tip_offset, template=False, **df)

    @classmethod
    def from_blocktemplate(cls, d):
        d["tx"] = d["transactions"]
        df = {k: v for k, v in d.items() if k in Block.pick_fields}
        block = cls(**df)
        block.fee = d["coinbasevalue"] - block.subsidy
        block.calculate_sigops()
        return block

    @property
    def subsidy(self):
        subsidy = 50 * COIN
        halvings = int(self.height / HALVING_INTERVAL)
        if halvings >= 64:
            return 0
        subsidy >>= halvings
        return subsidy

    @property
    def reward(self):
        return int(self.subsidy + self.fee)

    def calculate_sigops(self):
        """
        Calculate sigops_cost for blocks returned via Bitcoind `getblocktemplate` RPC
        """
        if not self.template:
            logger.error("can't calculate sigops if not form `blocktemplate` from RPC")
            return
        for tx in self.tx:
            self.sigopscost += tx["sigops"]

    def get_fee(self, rpc):
        if self.template:
            logger.error("can't fetch fee for blocktemplate from RPC")
            return
        self.fee = rpc.getblockstats(self.height)["totalfee"]

    def _add_by_txid(self, txid: str, mempool):
        """
        Add a transaction to the block
        """
        if txid in self.tx:
            logger.warning(f"{txid} already in block, skipping")
            return
        self.tx[txid] = mempool[txid]
        self.fee += int(self.tx[txid].fees["base"] * COIN)
        self.size += self.tx[txid].vsize
        self.weight += self.tx[txid].weight
        self.sigopscost += mempool[txid].sigopscost
        logger.debug(f"added tx {txid} to block {self.height}")

    def add_transaction(self, txid: str, mempool):
        """
        Adds a complete transaction chain to the block and remove it from mempool
        """
        if txid in self.tx:
            return

        for ancestor_txid in mempool[txid].depends:
            self.add_transaction(ancestor_txid, mempool)

        # Add it to the block
        self._add_by_txid(txid, mempool)

        # Remove it from the mempool
        # mempool.remove_transaction(txid)
        logger.debug(f"added chain for tx {txid} to block {self.height}")
