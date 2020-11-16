import logging

from tabulate import tabulate
import rpc
import miner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


tip, mempool, tip_one_template = rpc.fetch_synced()

# subtract blocktemplate entries from mempool
mempool.remove_block_mempool(tip_one_template)

# build a template for block tip + 2
tip_two_template = miner.get_blocktemplate(
    mempool, tip.height + 1, tip.version, tip.hash
)

table = [
    ["reward", f"{tip.reward:,}", f"{tip_one_template.reward:,}", f"{tip_two_template.reward:,}"],
    ["fee", f"{tip.fee:,}", f"{tip_one_template.fee:,}", f"{tip_two_template.fee:,}"],
    ["% of block reward", f"{tip.fee/tip.reward:.3f}", f"{tip_one_template.fee / tip_one_template.reward:.3f}", f"{tip_two_template.fee / tip_two_template.reward:.3f}"],
    # ["weight", f"{block_tip.}"
]

table_headers = ["block", "tip", "tip +1", "tip + 2"]

print(f"\nChain tip at height:   {tip.height}")
print(f"Block subsidy is:      {tip.subsidy:,} satoshis")
print(
    f"\n{tabulate(table, headers=table_headers, tablefmt='github', colalign=('left', 'right', 'right', 'right'))}\n"
)
