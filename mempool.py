import logging
import attr

from consensus import COIN


logger = logging.getLogger(__name__)


@attr.s
class MempoolTransaction(object):
    """
    Represents a transaction in the mempool.
    """
    # TODO: add ancestorweight

    ignore_fields = ["bip125-replaceable", "wtxid", "unbroadcast", "fee"]

    fees = attr.ib()
    vsize = attr.ib()
    weight = attr.ib()
    modifiedfee = attr.ib()
    sigopscost = attr.ib()
    time = attr.ib()
    height = attr.ib()
    descendantcount = attr.ib()
    descendantsize = attr.ib()
    descendantfees = attr.ib()
    ancestorcount = attr.ib()
    ancestorsize = attr.ib()
    ancestorsigops = attr.ib()
    ancestorfees = attr.ib()
    depends = attr.ib()
    spentby = attr.ib()

    @classmethod
    def from_json(cls, d: dict):
        """
        Load from a json (dict) representation.
        """
        df = {k: v for k, v in d.items() if k not in MempoolTransaction.ignore_fields}
        return cls(**df)

    @property
    def fee_rate(self):
        return self.ancestorfees / self.ancestorsize


class Mempool(dict):
    """
    Represents a mempool.
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    @classmethod
    def from_json(cls, d: dict):
        """
        Load from a json (dict) mempool dump from Core RPC `getrawmempool True`.
        """
        df = {k: MempoolTransaction.from_json(v) for k, v in d.items()}
        return cls(**df)

    @property
    def total_fee(self):
        return int(sum([tx.fees["base"] for tx in self.values()]) * COIN)

    @property
    def total_weight(self) -> int:
        return sum([tx.weight for tx in self.values()])

    @property
    def total_vsize(self) -> int:
        return sum([tx.vsize for tx in self.values()])

    @property
    def total_sigops(self):
        return sum([tx.sigopscost for tx in self.values()])

    def calculate_chain_weight(self, txid):
        weight = 0
        for ancestor_txid in self[txid].depends:
            weight += self.calculate_chain_weight(ancestor_txid)
        weight += self[txid].weight
        return weight

    def update_descendants(self, txid: str, fee: int, size: int, sigopscost: int, first: bool = False):
        """
        Update descendants' `ancestor fee/size/sigops` for a transaction being removed
        from the mempool.
        On the first recursion we also remove ourselves from `depends` of first
        children.
        """
        # If we have no descendants, just return
        if not self[txid].spentby:
            logger.debug(f"no descendants to update for {txid}")
            return

        # Each tx in txid.spentby should have (this) `txid` removed from it's depends
        if first:
            for child_txid in self[txid].spentby:
                self[child_txid].depends.remove(txid)
                logger.debug(f"removed {txid} from depends of descendant tx {child_txid}")

        # Decrement count, size, fee and sigops recursively
        for child_txid in self[txid].spentby:
            self[child_txid].ancestorcount -= 1
            self[child_txid].ancestorsize -= size
            self[child_txid].ancestorfees -= fee
            self[child_txid].ancestorsigops -= sigopscost
            self.update_descendants(child_txid, fee, size, sigopscost, first=False)
            logger.debug(f"updated tx {child_txid} descendant of tx {txid}")

    def remove_transaction(self, txid: str):
        """
        Removes a transaction from the mempool.
        Unlike Bitcoin Core, we *are* modifying the mempool in place so that we can
        create a second blocktemplate after the first.
        """
        if txid not in self:
            logger.error(f"not removed {txid} from mempool as not found")
            return
        # Remove ancestor fee/size from descendants
        self.update_descendants(
            txid=txid,
            fee=int(self[txid].fees["base"] * COIN),
            size=self[txid].vsize,
            sigopscost=self[txid].sigopscost,
            first=True,
        )

        del self[txid]
        logger.debug(f"removed {txid} from mempool and updated descendants")

    def remove_block(self, blocktemplate):
        """
        Intersects transactions in a `blocktemplate` and `mempool`
        """
        logger.debug(f"starting intersection of blocktemplate and mempool")

        i = 0
        for transaction in blocktemplate.tx:
            self.remove_transaction(transaction["txid"])
            i += 1
        logger.info(f"deleted {i} transactions from mempool after intersection")
        logger.info(f"mempool has {len(self)} transactions remaining")