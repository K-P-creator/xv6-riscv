#!/usr/bin/env python3
"""Replay observed writes to an address or display integer-array snapshots."""

import argparse
from pathlib import Path

from trace_common import load_trace, memory_rows, parse_int


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="QEMU trace CSV")
    parser.add_argument("--address", help="show writes to this exact address")
    parser.add_argument("--array-base", help="base address of a little-endian int array")
    parser.add_argument("--count", type=int, help="number of 4-byte array elements")
    args = parser.parse_args()
    if args.address is None and args.array_base is None:
        parser.error("provide --address or --array-base")
    if (args.array_base is None) != (args.count is None):
        parser.error("--array-base and --count must be supplied together")
    if args.count is not None and args.count < 1:
        parser.error("--count must be positive")

    mem = memory_rows(load_trace(args.trace))
    if args.address is not None:
        address = parse_int(args.address)
        known_value = None
        print(f"Writes to 0x{address:x}:")
        for row in mem:
            if row["operation"] == "write" and parse_int(row["address"]) == address:
                known_value = row["value"]
                print(
                    f"  row {row['_row']}: {row['size']}B value={known_value}"
                )
        if known_value is None:
            print("  no exact-address writes were recorded")
        else:
            print(f"Last observed value: {known_value}")

    if args.array_base is not None:
        base = parse_int(args.array_base)
        state: list[int | None] = [None] * args.count
        print(
            f"\n4-byte array snapshots at 0x{base:x} "
            f"(displayed values are unsigned bit patterns):"
        )
        for row in mem:
            if row["operation"] != "write" or int(row["size"]) != 4:
                continue
            address = parse_int(row["address"])
            offset = address - base
            if offset < 0 or offset % 4 or offset // 4 >= args.count:
                continue
            state[offset // 4] = parse_int(row["value"]) & 0xFFFFFFFF
            rendered = ", ".join(
                "?" if value is None else str(value) for value in state
            )
            print(f"  row {row['_row']}: [{rendered}]")
        if all(value is None for value in state):
            print("  no matching aligned 4-byte writes were recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
