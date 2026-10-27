#!/usr/bin/env python3
"""Map traced user/memory PCs to the nearest preceding executable symbol."""

import argparse
from collections import defaultdict
from pathlib import Path

from trace_common import load_symbols, load_trace, parse_int, symbol_for_pc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="QEMU trace CSV")
    parser.add_argument("symbols", type=Path, help="executable .sym file")
    parser.add_argument("--pc", help="show only this PC instead of grouping trace PCs")
    args = parser.parse_args()

    symbols = load_symbols(args.symbols)
    if not symbols:
        parser.error(f"no symbols found in {args.symbols}")
    if args.pc is not None:
        pc = parse_int(args.pc)
        print(f"0x{pc:x}: {symbol_for_pc(pc, symbols)}")
        return 0

    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in load_trace(args.trace):
        if row["record"] not in {"user", "mem"}:
            continue
        pc = parse_int(row["pc"])
        key = (row["record"], symbol_for_pc(pc, symbols))
        groups[key].append(pc)

    for (record, symbol), pcs in sorted(groups.items()):
        print(
            f"{record:4} {symbol:24} "
            f"{len(pcs):5} records, PCs 0x{min(pcs):x}..0x{max(pcs):x}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
