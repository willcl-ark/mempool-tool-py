import logging

from tabulate import tabulate
import rpc
import miner

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


previous, tip, template, mempool = rpc.fetch_synced()

# subtract blocktemplate entries from mempool
mempool.remove_block(template)

# build a template for block tip + 2
tip_two = miner.get_blocktemplate(mempool, tip.height + 1, tip.version, tip.hash)

for tx in template.tx:
    assert tx not in tip.tx

for tx in tip_two.tx:
    assert tx not in template.tx


blocks = [previous, tip, template, tip_two]


table = [
    ["reward"],                 # 0
    ["subsidy"],                # 1
    ["fee"],                    # 2
    ["% of block reward"],      # 3
    ["% reward/previous", f"", f"{100*(tip.reward / previous.reward):.3f}", f"{100*(template.reward/tip.reward):.3f}", f"{100*(tip_two.reward/template.reward):.3f}"],
    ["weight"],                 # 5
    ["sigops", "N/A", "N/A"],   # 6
]

table[0].extend([f"{block.reward:,}" for block in blocks])
table[1].extend([f"{block.subsidy:,}" for block in blocks])
table[2].extend([f"{block.fee:,}" for block in blocks])
table[3].extend([f"{100*(block.fee / block.reward):.3}" for block in blocks])
table[5].extend([f"{block.weight:,}" for block in blocks])
table[6].extend([f"{block.sigopscost:,}" for block in blocks[2:]])

table_headers = ["block:", previous.height, tip.height, "tip + 1", "tip + 2"]

print(
    f"\n{tabulate(table, headers=table_headers, tablefmt='github', colalign=('left', 'right', 'right', 'right', 'right'))}\n"
)
