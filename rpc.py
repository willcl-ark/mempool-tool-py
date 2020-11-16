import logging

from authproxy import AuthServiceProxy
from block import Block
from mempool import Mempool
from miner import check_mempool
from private import rpc_user, rpc_password


logger = logging.getLogger(__name__)
logging.getLogger("BitcoinRPC").setLevel(logging.INFO)


rpc = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_password))


def fetch_synced() -> (Block, Mempool, Block):
    """
    Fetches various data from Bitcoin Core RPC.
    Will check that tip_height before and after the fetch match, if they don't we assume
    a block was found between calls and try again.
    """
    tip_height, _height_check = 0, 1
    tip, mempool, blocktemplate = None, None, None
    mempool_ok = False

    while not tip_height == _height_check and not mempool_ok:
        tip_height = rpc.getblockcount()
        tip_hash = rpc.getbestblockhash()
        mempool = Mempool.from_json(rpc.getrawmempool(True))
        logger.debug(f"Got mempool dump with {len(mempool)} transactions")
        blocktemplate = Block.from_blocktemplate(
            rpc.getblocktemplate({"rules": ["segwit"]})
        )
        logger.debug(f"Got blocktemplate with {len(blocktemplate.tx)} transactions")
        _height_check = rpc.getblockcount()

        if not tip_height == _height_check:
            logger.debug(
                f"Block found between block template and mempool dump, retrying"
            )
        else:
            mempool_ok = check_mempool(mempool)
            tip = Block.from_getblock(rpc.getblock(tip_hash))
            tip.get_fee(rpc)

    return tip, mempool, blocktemplate