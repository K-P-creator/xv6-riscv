#!/usr/bin/env python3
"""Summarize record types, memory operations, PCs, and addresses in a QEMU trace."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from trace_common import load_symbols, load_trace, memory_rows, parse_int, symbol_for_pc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="QEMU trace CSV")
    parser.add_argument("--symbols", type=Path, help="optional executable .sym file")
    parser.add_argument("--top", type=int, default=10, help="number of busiest PCs/addresses")
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be positive")

    rows = load_trace(args.trace)
    symbols = load_symbols(args.symbols)
    mem = memory_rows(rows)
    print(f"Records: {dict(Counter(row['record'] for row in rows))}")
    print(f"Memory operations: {dict(Counter((r['operation'], r['size']) for r in mem))}")

    by_pc: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in mem:
        by_pc[parse_int(row["pc"])].append(row)
    print(f"\nTop {args.top} memory PCs:")
    for pc, accesses in Counter({pc: len(accesses) for pc, accesses in by_pc.items()}).most_common(args.top):
        label = symbol_for_pc(pc, symbols) if symbols else "unmapped"
        ops = Counter((row["operation"], row["size"]) for row in by_pc[pc])
        print(f"  0x{pc:x} ({label}): {len(by_pc[pc])} {dict(ops)}")

    by_address: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in mem:
        by_address[parse_int(row["address"])].append(row)
    print(f"\nTop {args.top} accessed addresses:")
    for address, accesses in Counter(
        {address: len(accesses) for address, accesses in by_address.items()}
    ).most_common(args.top):
        values = sorted({row["value"] for row in by_address[address]})
        ops = Counter(row["operation"] for row in by_address[address])
        examples = ", ".join(values[:4])
        if len(values) > 4:
            examples += ", ..."
        print(
            f"  0x{address:x}: {accesses} {dict(ops)} "
            f"distinct values={len(values)} [{examples}]"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
