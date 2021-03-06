import logging
from typing import Tuple

from authproxy import AuthServiceProxy
from block import Block
from mempool import Mempool
from private import rpc_user, rpc_password


logger = logging.getLogger(__name__)
logging.getLogger("BitcoinRPC").setLevel(logging.INFO)


rpc = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_password))


def fetch_synced() -> Tuple[dict, Block, Block, Mempool]:
    """
    Fetches various data from Bitcoin Core RPC.
    Will check that tip_height before and after the fetches match, if they don't a block
     was found between calls and try again.
    """
    tip_height, _height_check = 0, 1
    previous, tip, blocktemplate, mempool = None, None, None, None
    mempool_ok = False

    while not tip_height == _height_check and not mempool_ok:
        tip_height = rpc.getblockcount()
        tip_hash = rpc.getbestblockhash()

        # First get blocktemplate as it's a subset of mempool
        blocktemplate = Block.from_blocktemplate(rpc.getblocktemplate({"rules": ["segwit"]}))
        blocktemplate.height = tip_height + 1
        blocktemplate.tip_offset = "+ 1"
        logger.info(f"got blocktemplate with {len(blocktemplate.tx)} transactions")

        # Get a raw dump of the mempool
        mempool = Mempool.from_json(rpc.getrawmempool(True))
        logger.info(f"got mempool dump with {len(mempool)} transactions")

        # Check if a block was found between RPCs
        _height_check = rpc.getblockcount()
        if not tip_height == _height_check:
            logger.warning(f"block found between getblocktemplate and getrawmempool")
            continue

        # Now populate block data for the tip and 'tip - 1'
        tip = Block.from_getblock(rpc.getblock(tip_hash), tip_offset=u"\u2193")
        tip.get_fee(rpc)
        previous = Block.from_getblock(rpc.getblock(rpc.getblockstats(tip_height-1)["blockhash"]), tip_offset="- 1")
        previous.get_fee(rpc)

    return previous, tip, blocktemplate, mempool
