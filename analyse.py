from tabulate import tabulate


def print_blocks(blocks: list):
    blocks = sorted(blocks, key=lambda block: block.height)

    for i in range(len(blocks)):
        if i == 0:
            blocks[i].ratio = 0.0
        else:
            blocks[i].ratio = blocks[i].reward / blocks[i-1].reward

    table = [
        ["tip offset"],             # 0
        ["reward"],                 # 1
        ["subsidy"],                # 2
        ["fee"],                    # 3
        ["fee / block reward"],     # 4
        ["reward / prev block"],    # 5
        ["weight"],                 # 6
        ["sigops", "N/A", "N/A"],   # 7
    ]

    table[0].extend([block.tip_offset for block in blocks])
    table[1].extend([f"{block.reward:,}" for block in blocks])
    table[2].extend([f"{block.subsidy:,}" for block in blocks])
    table[3].extend([f"{block.fee:,}" for block in blocks])
    table[4].extend([f"{100*(block.fee / block.reward):.3}" for block in blocks])
    table[5].extend([f"{100*block.ratio:.3f}" for block in blocks])
    table[6].extend([f"{block.weight:,}" for block in blocks])
    table[7].extend([f"{block.sigopscost:,}" for block in blocks[2:]])

    table_headers = ["block:"]
    table_headers.extend([block.height for block in blocks])

    align = ["left"]
    align.extend(["right" for b in blocks])

    print(
        f"\n{tabulate(table, headers=table_headers, tablefmt='github', colalign=align)}\n"
    )
