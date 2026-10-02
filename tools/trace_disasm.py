#!/usr/bin/env python3
"""Print each traced memory access with its corresponding disassembly instruction."""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from trace_common import format_access, load_symbols, load_trace, memory_rows


OBJDUMP_CANDIDATES = (
    "riscv64-unknown-elf-objdump",
    "riscv64-linux-gnu-objdump",
    "riscv64-elf-objdump",
    "objdump",
)


def read_disassembly(binary: Path) -> dict[int, str]:
    objdump = next(
        (path for name in OBJDUMP_CANDIDATES if (path := shutil.which(name))),
        None,
    )
    if objdump is None:
        raise RuntimeError("could not find a RISC-V objdump executable")
    result = subprocess.run(
        [objdump, "-d", str(binary)],
        check=True,
        capture_output=True,
        text=True,
    )
    instructions: dict[int, str] = {}
    for line in result.stdout.splitlines():
        match = re.match(r"^\s*([0-9a-fA-F]+):\s+(.+)$", line)
        if match:
            instructions[int(match.group(1), 16)] = line.strip()
    return instructions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="QEMU trace CSV")
    parser.add_argument("binary", type=Path, help="ELF executable used for the trace")
    parser.add_argument("--symbols", type=Path, help="optional executable .sym file")
    args = parser.parse_args()
    if not args.binary.is_file():
        parser.error(f"executable does not exist: {args.binary}")

    try:
        instructions = read_disassembly(args.binary)
    except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
        print(f"trace_disasm.py: {error}", file=sys.stderr)
        return 1

    symbols = load_symbols(args.symbols)
    rows = load_trace(args.trace)
    for row in memory_rows(rows):
        pc = int(row["pc"], 0)
        instruction = instructions.get(pc, "<instruction PC not found in disassembly>")
        print(f"{format_access(row, symbols)}\n    {instruction}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
