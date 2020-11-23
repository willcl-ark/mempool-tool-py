import logging
from time import perf_counter

from tabulate import tabulate

from block import Block, COINBASE_WEIGHT, COINBASE_SIGOPS
from consensus import MAX_BLOCK_WEIGHT, MAX_BLOCK_SIGOPS_COST, WITNESS_SCALE_FACTOR
from mempool import Mempool


logger = logging.getLogger(__name__)
MAX_BLOCK_SIZE = int(MAX_BLOCK_WEIGHT / WITNESS_SCALE_FACTOR)


def check_mempool(mempool) -> bool:
    """
    Checks mempool consistency. We must have all transactions listed as `depends`
    but we also check `spentby` to make the program simpler later
    """
    for txid in mempool.keys():
        for _txid in mempool[txid].depends:
            if _txid not in mempool.keys():
                logger.error(f"{_txid} missing from mempool listed as 'depends' for {txid}")
                return False
        for _txid in mempool[txid].spentby:
            if _txid not in mempool.keys():
                logger.error(f"{_txid} missing from mempool listed as 'spentby' for {txid}")
                return False
    logger.debug(f"mempool check succeeded")
    return True


def sorted_mempool_list(mempool: Mempool) -> list:
    """
    Sorts a mempool by 'fee_rate' and returns txids in a list
    """
    return [
        txid
        for txid, value in sorted(
            mempool.items(), key=lambda tx: tx[1].fee_rate, reverse=True
        )
    ]


def create_block(mempool, height, version, previousblockhash) -> Block:
    """
    Create a new block based on a sorted transaction list
    """
    # Limit failed tries in case we have a large mempool
    MAX_TRIES = 1000

    block = Block(height, version, dict(), previousblockhash)

    # Sort the mempool by `chain_fee_vsize`
    sorted_list = sorted_mempool_list(mempool)

    tries = 0
    while sorted_list and tries < MAX_TRIES:
        # Smallest tx size dictated by standard node policy
        if block.weight > MAX_BLOCK_WEIGHT - 82:
            logger.debug(f"cannot fit any more standard transactions into block")
            break

        txid = sorted_list.pop(0)
        if txid in block.tx:
            logger.debug(f"cannot add existing transaction {txid} to block {height}")
            continue

        # Check we can fit the weight of the tx chain.
        # Below appears to be how Bitcoin Core does it; checking vsize * SCALE_FACTOR
        # # TODO: switch this to ancestorweight
        _chain_weight = mempool[txid].ancestorsize * WITNESS_SCALE_FACTOR
        if not block.weight + _chain_weight < MAX_BLOCK_WEIGHT:
            logger.debug(f"cannot fit tx chain for {txid} of weight {_chain_weight} into block with {MAX_BLOCK_WEIGHT - block.weight} weight units remaining")
            tries += 1
            continue

        # Check we can fit the total SigOps of the tx chain
        _sigops_cost = mempool[txid].ancestorsigops
        if not block.sigopscost + _sigops_cost < MAX_BLOCK_SIGOPS_COST:
            logger.debug(f"cannot fit tx chain for {txid} with {_sigops_cost} sigops in block with {MAX_BLOCK_SIGOPS_COST - block.sigopscost} sigops remaining")
            tries += 1
            continue

        # Add the chain to the block
        block.add_transaction(txid, mempool)

        # Re-sort the mempool
        # sorted_list = sorted_mempool_list(mempool)

    return block


def print_block_stats(block: Block, mempool_fee, mempool_weight, mempool_vsize, mempool_tx_count, mempool_sigops_count):
    print("\nBlock stats:\n")
    table = [
        ["transactions", f"{mempool_tx_count:,}",     f"{len(block.tx):,}",       f""],
        ["fee",          f"{mempool_fee:,}",          f"{block.fee:,}",           f""],
        ["weight",       f"{mempool_weight:,}",       f"{block.weight:,}",        f"{MAX_BLOCK_WEIGHT:,}"],
        ["vsize",        f"{mempool_vsize:,}",        f"{block.size:,}",          f"{MAX_BLOCK_SIZE:,}"],
        ["sigops",       f"{mempool_sigops_count:,}", f"{block.sigopscost:,}", f"{MAX_BLOCK_SIGOPS_COST:,}"]
    ]
    table_headers = ["", "mempool", "tip + 1", "limit"]
    print(f"\n{tabulate(table, headers=table_headers, tablefmt='github', colalign=('left', 'right', 'right', 'right'))}\n")


def check_block(block: Block):
    # Allocate for coinbase transaction
    weight = COINBASE_WEIGHT
    sigops = COINBASE_SIGOPS
    fee = 0
    invalid = False

    # Check each transaction in the block
    for transaction in block.tx.values():
        # Sum the vsize and fee
        weight += transaction.weight
        fee += transaction.fees["base"]
        sigops += transaction.sigopscost
        # If it has ancestors, check each ancestor is present
        for txid in transaction.depends:
            assert txid in block.tx

    if weight > MAX_BLOCK_WEIGHT:
        logger.error(f"weight: {weight:,} > {MAX_BLOCK_WEIGHT:,}")
        invalid = True
    if sigops > MAX_BLOCK_SIGOPS_COST:
        logger.error(f"sigops: {sigops:,} > {MAX_BLOCK_SIGOPS_COST:,}")
        invalid = True

    if invalid:
        logger.error("Block invalid!")
        return False

    logger.info("Block valid!")
    return True


def get_blocktemplate(mempool: Mempool, height, version, previousblockhash) -> Block:
    m_fee = mempool.total_fee
    m_weight = mempool.total_weight
    m_vsize = mempool.total_vsize
    m_tx = len(mempool)
    m_sigops = mempool.total_sigops
    logger.debug(f"{m_fee:,} total fees in mempool for blocktemplate")
    logger.debug(f"{m_vsize:,} total vsize in mempool for blocktemplate")
    logger.debug(f"{m_weight:,} total weight in mempool for blocktemplate")
    logger.debug(f"{m_sigops:,} total sigops in mempool for blocktemplate")

    tic = perf_counter()
    block = create_block(mempool, height, version, previousblockhash)
    toc = perf_counter()
    logger.info(f"Block assembly took {toc - tic:.5f} seconds")

    # Print block stats
    print_block_stats(block, m_fee, m_weight, m_vsize, m_tx, m_sigops)

    # Check the block is valid
    check_block(block)

    return block
