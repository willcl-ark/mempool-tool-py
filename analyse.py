import math
from tabulate import tabulate


def estimate_reorg(val, hash_pow):
    """
    Estimate how likely someone is to perhaps try a re-org.
    """
    # Error function: https://en.wikipedia.org/wiki/Error_function

    # Add a scaling factor of 75/hash_pow, this gives a 50% chance of re-org when fees
    # of current block` are 1.5x fees of `next block` for hash_power of 50%

    # 75% hashpower: scale = 1
    # 50% hashpower: scale = 1.5
    # 25% hashpower: scale = 2
    scale = 75 / hash_pow

    return math.erf(val - scale)


def print_blocks(blocks: list):
    blocks = sorted(blocks, key=lambda block: block.height)

    for i in range(len(blocks)):
        if i == 0:
            blocks[i].ratio = 0.0
        else:
            blocks[i].ratio = blocks[i].reward / blocks[i-1].reward

    # Estimated reorg probability for 10, 25 and 50% hashpower miners
    for i in range(len(blocks)):
        if i == 0:
            blocks[i].reorg5 = 0
            blocks[i].reorg10 = 0
            blocks[i].reorg25 = 0
            blocks[i].reorg50 = 0
        else:
            reward_diff = blocks[i-1].reward / blocks[i].reward
            blocks[i].reorg5 = estimate_reorg(reward_diff, 5)
            blocks[i].reorg10 = estimate_reorg(reward_diff, 10)
            blocks[i].reorg25 = estimate_reorg(reward_diff, 25)
            blocks[i].reorg50 = estimate_reorg(reward_diff, 50)

    table = [
        ["tip offset"],             # 0
        ["reward"],                 # 1
        ["subsidy"],                # 2
        ["fee"],                    # 3
        ["fee / block reward"],     # 4
        ["reward / prev block"],    # 5
        ["weight"],                 # 6
        ["sigops", "N/A", "N/A"],   # 7
        ["reorg chance 5% hash"],       # 8
        ["reorg chance 10% hash"],       # 9
        ["reorg chance 25% hash"],       # 10
        ["reorg chance 50% hash"],       # 11
    ]

    table[0].extend([block.tip_offset for block in blocks])
    table[1].extend([f"{block.reward:,}" for block in blocks])
    table[2].extend([f"{block.subsidy:,}" for block in blocks])
    table[3].extend([f"{block.fee:,}" for block in blocks])
    table[4].extend([f"{100*(block.fee / block.reward):.3}" for block in blocks])
    table[5].extend([f"{100*block.ratio:.3f}" for block in blocks])
    table[6].extend([f"{block.weight:,}" for block in blocks])
    table[7].extend([f"{block.sigopscost:,}" for block in blocks[2:]])
    table[8].extend([f"{block.reorg5:.5f}" for block in blocks])
    table[9].extend([f"{block.reorg10:.5f}" for block in blocks])
    table[10].extend([f"{block.reorg25:.5f}" for block in blocks])
    table[11].extend([f"{block.reorg50:.5f}" for block in blocks])

    table_headers = ["block:"]
    table_headers.extend([block.height for block in blocks])

    align = ["left"]
    align.extend(["right" for b in blocks])

    print(
        f"\n{tabulate(table, headers=table_headers, tablefmt='github', colalign=align)}\n"
    )

