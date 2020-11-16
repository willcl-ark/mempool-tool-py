import logging
from time import perf_counter

from block import Block
from consensus import MAX_BLOCK_WEIGHT
from mempool import Mempool


logger = logging.getLogger(__name__)
MAX_BLOCK_SIZE = int(MAX_BLOCK_WEIGHT / 4)


def check_mempool(mempool) -> bool:
    """
    Checks mempool consistency. We must have all transactions listed as `depends`
    but we also check `spentby` to make the program simpler later
    """
    for txid in mempool.keys():
        for _txid in mempool[txid].depends:
            if _txid not in mempool.keys():
                logger.error(
                    f"{_txid} missing from mempool listed as 'depends' for {txid}"
                )
                return False
        for _txid in mempool[txid].spentby:
            if _txid not in mempool.keys():
                logger.error(
                    f"{_txid} missing from mempool listed as 'spentby' for {txid}"
                )
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
    # Limit tries if we have a large mempool
    MAX_TRIES = 1000

    block = Block(height, version, dict(), previousblockhash)
    block.init_coinbase()

    # Sort the mempool by `chain_fee_weight`
    sorted_list = sorted_mempool_list(mempool)

    tries = 0
    while sorted_list and block.weight < MAX_BLOCK_SIZE and tries < MAX_TRIES:
        txid = sorted_list.pop(0)

        if txid in block.tx:
            logger.debug(f"cannot add existing transaction {txid} to block {height}")
            continue

        # Check we will fit the whole chain
        _chain_size = mempool[txid].ancestorsize
        if not block.weight + _chain_size < MAX_BLOCK_SIZE:
            logger.debug(
                f"cannot fit chain size {_chain_size} in block for tx {txid}, skipping"
            )
            tries += 1
            continue

        # Add the chain to the block
        block.add_chain(txid, mempool)

        # Re-sort the mempool
        # sorted_list = sorted_mempool_list(mempool)

    return block


def print_block_stats(block: Block, total_fee, total_weight, num_mempool_tx):
    print("\nBlock stats:\n")
    print(f"Transactions: {len(block.tx)} / {num_mempool_tx}")
    print(f"Fee:          {int(block.fee):,} / {total_fee:,}")
    print(f"vsize:        {block.weight:,} / {total_weight:,}")


def check_block(block: Block):
    # Allocate for coinbase transaction
    vsize_sum = 1000
    fee_sum = 0

    # Check each transaction in the block
    for transaction in block.tx.values():
        # Sum the vsize and fee
        vsize_sum += transaction.vsize
        fee_sum += transaction.fees["base"]

        # If it has ancestors, check each ancestor is present
        for txid in transaction.depends:
            assert txid in block.tx

    try:
        assert vsize_sum <= MAX_BLOCK_SIZE
    except AssertionError:
        print("\n\tBlock invalid!\n")
        print(f"Vsize: {vsize_sum} > {MAX_BLOCK_SIZE}")
    else:
        print("\n\tBlock valid!\n")


def get_blocktemplate(mempool: Mempool, height, version, previousblockhash) -> Block:
    m_fee = mempool.total_fee
    m_weight = mempool.total_weight
    m_tx = len(mempool)
    logger.debug(f"{m_fee} total fees in mempool for blocktemplate")
    logger.debug(f"{m_weight} total weight in mempool for blocktemplate")

    tic = perf_counter()
    block = create_block(mempool, height, version, previousblockhash)
    toc = perf_counter()
    print(f"Block assembly took {toc - tic:.5f} seconds")

    # Print block stats
    print_block_stats(block, m_fee, m_weight, m_tx)

    # Check the block is valid
    check_block(block)

    return block
