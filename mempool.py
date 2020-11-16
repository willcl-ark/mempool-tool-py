import logging
import attr

from consensus import COIN


logger = logging.getLogger(__name__)


@attr.s
class MempoolTransaction(object):
    """
    Represents a transaction in the mempool.
    """

    ignore_fields = ["bip125-replaceable", "wtxid", "unbroadcast", "fee"]

    fees = attr.ib()
    vsize = attr.ib()
    weight = attr.ib()
    modifiedfee = attr.ib()
    time = attr.ib()
    height = attr.ib()
    descendantcount = attr.ib()
    descendantsize = attr.ib()
    descendantfees = attr.ib()
    ancestorcount = attr.ib()
    ancestorsize = attr.ib()
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

    def update_descendants(self, txid: str, fee: int, size: int, first: bool = False):
        """
        Update descendants' `ancestor fee/size` fields, and `depends` for a transaction
        being removed from the mempool. On the first recursion we also remove ourselves
        from `depends` of first children.
        """
        # If we have no descendants, just return
        if not self[txid].spentby:
            logger.debug(f"no descendants to update for {txid}")
            return

        # On first recursion, tx spending `txid` should have `txid` removed from depends
        if first:
            for child_txid in self[txid].spentby:
                self[child_txid].depends.remove(txid)
                logger.debug(f"removed {txid} from depends of {child_txid}")

        # Decrement count, size and fee recursively
        for child_txid in self[txid].spentby:
            self[child_txid].ancestorcount -= 1
            self[child_txid].ancestorsize -= size
            self[child_txid].ancestorfees -= fee
            self.update_descendants(child_txid, fee, size, first=False)
            # logger.debug(f"updated tx {child_txid} descendant of tx {txid}")

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
            first=True,
        )

        del self[txid]
        logger.debug(f"removed {txid} from mempool and updated descendants")

    def remove_block_mempool(self, blocktemplate):
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