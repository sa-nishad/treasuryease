"""Command-line interface: ``camt-twist-parser statement.xml -o fees.csv``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .core import (
    ParseError,
    build_table,
    parse_xml,
    row_element_options,
    summary_lines,
    to_csv,
    to_json,
)

DELIMS = {"comma": ",", "semicolon": ";", "tab": "\t", "pipe": "|"}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="camt-twist-parser",
        description="Convert camt.086 and TWIST bank service billing XML to CSV or JSON.",
    )
    p.add_argument("files", nargs="+", type=Path, help="one or more XML files")
    p.add_argument("-o", "--output", type=Path, help="output file (default: standard output)")
    p.add_argument("-f", "--format", choices=["csv", "json"], help="output format (default: from --output extension, else csv)")
    p.add_argument("--row-element", default="auto", metavar="NAME", help="element that becomes one row, for example Svc (default: auto-detect)")
    p.add_argument("--list-elements", action="store_true", help="list candidate row elements and exit")
    p.add_argument("--no-context", action="store_true", help="do not repeat header and statement fields on every row")
    p.add_argument("--no-source", action="store_true", help="do not add the Source_file column")
    p.add_argument("--include-addresses", action="store_true", help="include postal address fields (skipped by default)")
    p.add_argument("--signed", action="store_true", help="add signed amount columns (DBIT becomes negative)")
    p.add_argument("--naming", choices=["short", "full"], default="short", help="column naming style")
    csvg = p.add_argument_group("CSV options")
    csvg.add_argument("--delimiter", choices=list(DELIMS), default="comma")
    csvg.add_argument("--quote-all", action="store_true", help="quote every field")
    csvg.add_argument("--lf", action="store_true", help="use LF line endings instead of CRLF")
    csvg.add_argument("--no-header", action="store_true", help="omit the header row")
    csvg.add_argument("--decimal-comma", action="store_true", help="write amounts with a decimal comma")
    csvg.add_argument("--bom", action="store_true", help="write a UTF-8 byte order mark (for Excel)")
    jsg = p.add_argument_group("JSON options")
    jsg.add_argument("--amounts-as-text", action="store_true", help="keep amounts as strings")
    jsg.add_argument("--compact", action="store_true", help="no indentation")
    p.add_argument("--summary", action="store_true", help="print row counts and totals to standard error")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    parsed = []
    for path in args.files:
        try:
            parsed.append(parse_xml(path))
        except (OSError, ParseError) as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            return 2

    if args.list_elements:
        for name, count in row_element_options(parsed):
            print(f"{name}\t{count}")
        return 0

    table = build_table(
        parsed,
        row_element=args.row_element,
        context=not args.no_context,
        source_column=not args.no_source,
        signed=args.signed,
        naming=args.naming,
        include_addresses=args.include_addresses,
    )

    fmt = args.format or (
        "json" if args.output and args.output.suffix.lower() == ".json" else "csv"
    )
    if fmt == "json":
        text = to_json(table, numbers=not args.amounts_as_text, indent=None if args.compact else 2)
    else:
        text = to_csv(
            table,
            delimiter=DELIMS[args.delimiter],
            quote_all=args.quote_all,
            eol="\n" if args.lf else "\r\n",
            header=not args.no_header,
            decimal="," if args.decimal_comma else ".",
        )
        if args.bom:
            text = "﻿" + text

    if args.output:
        args.output.write_bytes(text.encode("utf-8"))
    else:
        sys.stdout.buffer.write(text.encode("utf-8"))

    if args.summary or table.warnings:
        for line in summary_lines(table):
            print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
