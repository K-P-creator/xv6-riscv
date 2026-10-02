"""Shared helpers for inspecting xv6 QEMU trace CSV files."""

import csv
import re
from pathlib import Path
from typing import Iterable


TRACE_FIELDS = {"record", "vcpu", "pc", "address", "size", "operation", "value"}
NON_FUNCTION_SYMBOLS = {
    ".text",
    ".rodata",
    ".data",
    ".bss",
    ".eh_frame",
    ".debug_info",
    ".debug_abbrev",
    ".debug_loc",
    ".debug_aranges",
    ".debug_line",
    ".debug_str",
    ".comment",
    ".riscv.attributes",
}


def parse_int(value: str) -> int:
    return int(value, 0)


def load_trace(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as trace_file:
        reader = csv.DictReader(trace_file)
        missing = TRACE_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"trace is missing CSV columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    for row_number, row in enumerate(rows, start=2):
        row["_row"] = str(row_number)
        if row["record"] not in {"kernel", "user", "mem"}:
            raise ValueError(f"line {row_number}: unknown record type {row['record']!r}")
        if row["record"] == "mem":
            for field in ("pc", "address", "size", "value"):
                try:
                    parse_int(row[field])
                except ValueError as error:
                    raise ValueError(
                        f"line {row_number}: invalid {field} value {row[field]!r}"
                    ) from error
            if row["operation"] not in {"read", "write"}:
                raise ValueError(
                    f"line {row_number}: invalid memory operation {row['operation']!r}"
                )
    return rows


def load_symbols(path: Path | None) -> list[tuple[int, str]]:
    if path is None:
        return []

    symbols: list[tuple[int, str]] = []
    for line in path.read_text().splitlines():
        match = re.match(r"^\s*(?:0x)?([0-9a-fA-F]+)\s+(\S+)\s*$", line)
        if match is None:
            continue
        address, name = match.groups()
        if name not in NON_FUNCTION_SYMBOLS and not name.endswith((".c", ".o")):
            symbols.append((int(address, 16), name))
    return sorted(symbols)


def symbol_for_pc(pc: int, symbols: list[tuple[int, str]]) -> str:
    preceding = [symbol for address, symbol in symbols if address <= pc]
    if not preceding:
        return "unknown"
    return preceding[-1]


def format_access(row: dict[str, str], symbols: list[tuple[int, str]]) -> str:
    pc = parse_int(row["pc"])
    label = symbol_for_pc(pc, symbols) if symbols else "unmapped"
    return (
        f"row={row['_row']} vcpu={row['vcpu']} pc=0x{pc:x} ({label}) "
        f"{row['operation']} {row['size']}B at {row['address']} = {row['value']}"
    )


def memory_rows(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row["record"] == "mem"]
