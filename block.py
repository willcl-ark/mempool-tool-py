import logging

import attr
from consensus import COIN, HALVING_INTERVAL


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
    tx = attr.ib(type=dict)
    previousblockhash = attr.ib(type=hex)
    hash = attr.ib(type=hex, default=64 * 0)
    size = attr.ib(type=int, default=0)
    weight = attr.ib(type=int, default=0)
    fee = attr.ib(type=int, default=0)
    template = attr.ib(type=bool, default=True)

    @classmethod
    def from_getblock(cls, d):
        df = {k: v for k, v in d.items() if k in Block.pick_fields}
        return cls(template=False, **df)

    @classmethod
    def from_blocktemplate(cls, d):
        d["tx"] = d["transactions"]
        df = {k: v for k, v in d.items() if k in Block.pick_fields}
        block = cls(**df)
        block.fee = d["coinbasevalue"] - block.subsidy
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

    def get_fee(self, rpc):
        if self.template:
            logger.error("can't fetch fee for blocktemplate from RPC")
            return
        self.fee = rpc.getblockstats(self.height)["totalfee"]

    def init_coinbase(self):
        self.weight += 1000

    def add_transaction(self, txid, mempool):
        """
        Adds a transaction to the block
        """
        if txid in self.tx:
            logger.debug(f"{txid} already in block, skipping")
            return
        self.tx[txid] = mempool[txid]
        _fee = int(self.tx[txid].fees["base"] * COIN)
        _vsize = self.tx[txid].vsize
        self.fee += _fee
        self.weight += _vsize
        logger.debug(f"added tx {txid} to block {self.height}")

    def add_chain(self, txid: str, mempool):
        """
        Adds a complete transaction chain to the block and remove it from mempool
        """
        for ancestor_txid in mempool[txid].depends:
            self.add_chain(ancestor_txid, mempool)
            self.add_transaction(ancestor_txid, mempool)
            # mempool.remove_transaction(ancestor_txid)

        self.add_transaction(txid, mempool)
        # mempool.remove_transaction(txid)
        logger.debug(f"added chain for tx {txid} to block {self.height}")
