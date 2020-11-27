import math
from tabulate import tabulate


def estimate_reorg(val):
    # Estimate how likely someone is to perhaps try a re-org.
    # This does not consider hash power which would also affect the likelihood.
    # Error function: https://en.wikipedia.org/wiki/Error_function
    # Add a scaling factor of 1.5, this gives a 50% chance of re-org when fees
    # of current block` are 1.5x fees of `next block`
    scale = 1.5
    return math.erf(val - scale)


def print_blocks(blocks: list):
    blocks = sorted(blocks, key=lambda block: block.height)

    for i in range(len(blocks)):
        if i == 0:
            blocks[i].ratio = 0.0
        else:
            blocks[i].ratio = blocks[i].reward / blocks[i-1].reward

    for i in range(len(blocks)):
        if i == 0:
            blocks[i].reorg = 0
        else:
            reward_diff = blocks[i-1].reward / blocks[i].reward
            blocks[i].reorg = estimate_reorg(reward_diff)

    table = [
        ["tip offset"],             # 0
        ["reward"],                 # 1
        ["subsidy"],                # 2
        ["fee"],                    # 3
        ["fee / block reward"],     # 4
        ["reward / prev block"],    # 5
        ["weight"],                 # 6
        ["sigops", "N/A", "N/A"],   # 7
        ["reorg chance"],           # 8
    ]

    table[0].extend([block.tip_offset for block in blocks])
    table[1].extend([f"{block.reward:,}" for block in blocks])
    table[2].extend([f"{block.subsidy:,}" for block in blocks])
    table[3].extend([f"{block.fee:,}" for block in blocks])
    table[4].extend([f"{100*(block.fee / block.reward):.3}" for block in blocks])
    table[5].extend([f"{100*block.ratio:.3f}" for block in blocks])
    table[6].extend([f"{block.weight:,}" for block in blocks])
    table[7].extend([f"{block.sigopscost:,}" for block in blocks[2:]])
    table[8].extend([f"{block.reorg:.5f}" for block in blocks])

    table_headers = ["block:"]
    table_headers.extend([block.height for block in blocks])

    align = ["left"]
    align.extend(["right" for b in blocks])

    print(
        f"\n{tabulate(table, headers=table_headers, tablefmt='github', colalign=align)}\n"
    )

