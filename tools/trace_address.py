#!/usr/bin/env python3
"""Show accesses to an address and, optionally, values used as pointers."""

import argparse
from pathlib import Path

from trace_common import format_access, load_symbols, load_trace, memory_rows, parse_int


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="QEMU trace CSV")
    parser.add_argument("address", help="guest virtual address, e.g. 0x5f78")
    parser.add_argument("--symbols", type=Path, help="optional executable .sym file")
    parser.add_argument(
        "--follow-pointer",
        action="store_true",
        help="also show accesses whose address equals a value read from this address",
    )
    args = parser.parse_args()
    address = parse_int(args.address)

    rows = load_trace(args.trace)
    mem = memory_rows(rows)
    symbols = load_symbols(args.symbols)
    direct = [row for row in mem if parse_int(row["address"]) == address]

    print(f"Accesses to 0x{address:x}: {len(direct)}")
    for row in direct:
        print(format_access(row, symbols))

    if args.follow_pointer:
        targets = {
            parse_int(row["value"])
            for row in direct
            if row["operation"] == "read"
        }
        targets.discard(address)
        for target in sorted(targets):
            indirect = [row for row in mem if parse_int(row["address"]) == target]
            print(f"\nAccesses to value 0x{target:x} read from 0x{address:x}: {len(indirect)}")
            for row in indirect:
                print(format_access(row, symbols))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
