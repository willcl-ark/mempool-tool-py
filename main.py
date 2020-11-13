from authproxy import AuthServiceProxy, JSONRPCException
from private import rpc_user, rpc_password

COIN = 100_000_000
HALVING_INTERVAL = 210_000


rpc = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_password))


def get_current_block_fee(block_height):
    """ Returns the current block fee in satoshis """
    return rpc.getblockstats(rpc.getblockcount())["totalfee"]


def get_next_block():
    """ Returns two items, the block template  of the next block and a json dump of the current mempool """
    return (rpc.getblocktemplate(), rpc.getrawmempool(True))


def exclude_template_from_mempool(template, mempool):
    """ Compares two sets of transactions, and removes those in the template from those in the mempool """
    # for transaction in template:
    #     mempool.delete
    pass


def calc_block_reward(block_height):
    """
    Calculates the block reward for a block
    e.g. calc_block_reward(rpc.getblockcount())
    """

    reward = 50 * COIN
    halvings = int(block_height / HALVING_INTERVAL)

    if halvings >= 64:
        return 0

    reward >>= halvings

    return reward
