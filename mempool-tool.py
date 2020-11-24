import logging

import analyse
import rpc
import miner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    previous, tip, template, mempool = rpc.fetch_synced()

    # Subtract blocktemplate entries from mempool
    mempool.remove_block(template)

    # Build a template for block tip + 2
    tip_two = miner.get_blocktemplate(mempool, tip.height + 2, tip.version, tip.hash)

    # Make a list
    blocks = [previous, tip, template, tip_two]

    analyse.print_blocks(blocks)


if __name__ == "__main__":
    main()
