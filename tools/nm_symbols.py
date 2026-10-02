#!/usr/bin/env python3
"""Print the symbol-to-address map for an xv6 executable."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


NM_CANDIDATES = (
    "riscv64-unknown-elf-nm",
    "riscv64-linux-gnu-nm",
    "nm",
)


def find_nm() -> str:
    for candidate in NM_CANDIDATES:
        path = shutil.which(candidate)
        if path is not None:
            return path
    raise RuntimeError("could not find a RISC-V nm executable")


def read_symbols(binary: Path, text_only: bool = False) -> dict[str, int]:
    nm = find_nm()
    result = subprocess.run(
        [nm, "-a", "-n", str(binary)],
        check=True,
        capture_output=True,
        text=True,
    )

    symbols: dict[str, int] = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue

        address, symbol_type, name = fields
        if text_only and symbol_type not in {"T", "t"}:
            continue
        try:
            symbols[name] = int(address, 16)
        except ValueError:
            continue

    return symbols


def render_template(template: str, symbols: dict[str, int]) -> str:
    rendered = template
    start = rendered.find("{{#symbols}}")
    end = rendered.find("{{/symbols}}")
    if start < 0 or end < start:
        raise ValueError("template must contain a {{#symbols}} block")

    block_start = start + len("{{#symbols}}")
    block = rendered[block_start:end]
    entries = []
    seen_addresses: set[int] = set()
    for name, address in symbols.items():
        if address in seen_addresses:
            continue
        seen_addresses.add(address)
        entries.append(
            block.replace("{{name}}", json.dumps(name))
            .replace("{{address}}", f"0x{address:016x}ULL")
        )
    rendered = rendered[:start] + "".join(entries) + rendered[end + len("{{/symbols}}"):]
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print an nm-derived symbol name to address map."
    )
    parser.add_argument("binary", type=Path, help="ELF executable to inspect")
    parser.add_argument(
        "--template",
        type=Path,
        help="Mustache-style C template to render from the symbol map",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for rendered template (requires --template)",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Include only text/function symbols",
    )
    args = parser.parse_args()

    if not args.binary.is_file():
        parser.error(f"input file does not exist: {args.binary}")
    if args.output is not None and args.template is None:
        parser.error("--output requires --template")

    try:
        symbols = read_symbols(args.binary, args.text_only)
    except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
        print(f"nm_symbols.py: {error}", file=sys.stderr)
        return 1

    if args.template is not None:
        try:
            rendered = render_template(args.template.read_text(), symbols)
            if args.output is None:
                print(rendered, end="")
            else:
                args.output.write_text(rendered)
        except (OSError, ValueError) as error:
            print(f"nm_symbols.py: {error}", file=sys.stderr)
            return 1
        return 0

    print("{")
    for name, address in symbols.items():
        print(f"    {name!r}: 0x{address:016x},")
    print("}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
