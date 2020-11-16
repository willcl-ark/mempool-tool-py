from authproxy import AuthServiceProxy, JSONRPCException
from private import rpc_user, rpc_password

COIN = 100_000_000
HALVING_INTERVAL = 210_000


rpc = AuthServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpc_user, rpc_password))


def get_current_block_fee(block_height: int) -> int:
    """ Returns the current block fee in satoshis """
    return rpc.getblockstats(block_height)["totalfee"]


def get_next_block() -> (dict, dict):
    """
    Returns two items:
    i) the block template of the next block
    ii) json dump of the current mempool
    """
    return rpc.getblocktemplate({"rules": ["segwit"]}), rpc.getrawmempool(True)


def intersect_template_mempool(template, mempool) -> None:
    """
    Intersects block template and mempool, modifying the mempool object in-place
    """
    template_txs = set()
    i = 0
    for transaction in template["transactions"]:
        template_txs.add(transaction["txid"])
        i += 1
    print(f"Parsed {i} transactions from template")

    i = 0
    for transaction in list(mempool):
        if transaction in template_txs:
            del mempool[transaction]
            i += 1
    print(f"Deleted {i} transactions from mempool after intersection of template and mempool")


def calc_block_reward(block_height: int) -> int:
    """
    Calculates the block reward for a block
    use e.g. calc_block_reward(rpc.getblockcount())
    """
    reward = 50 * COIN
    halvings = int(block_height / HALVING_INTERVAL)
    if halvings >= 64:
        return 0
    reward >>= halvings
    return reward


template, mempool = get_next_block()
intersect_template_mempool(template, mempool)
