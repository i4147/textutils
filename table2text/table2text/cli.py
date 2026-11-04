from __future__ import annotations

import argparse
import sys

from . import __version__
from .ast import parse
from .brief import DEFAULT_BUDGET, brief_with_facts
from .budget import _wide, count_tokens, floor_tokens, packed_best


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="table2text",
        description=(
            "Emit a compact, token-budgeted text brief of a messy CSV or "
            "xlsx workbook so an LLM agent can write a correct extractor "
            "without opening the file."
        ),
    )
    parser.add_argument("file", help="path to the CSV or .xlsx file")
    parser.add_argument(
        "--sheet",
        metavar="NAME_OR_INDEX",
        default=None,
        help=("xlsx only: worksheet to read, by name or 0-based position (default: the first visible sheet)"),
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        metavar="N",
        help=(
            f"hard upper bound on output tokens (default {DEFAULT_BUDGET}: "
            "the largest brief every major agent harness ingests in one "
            "untruncated read)"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the full table-AST as JSON instead of the text brief",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    if args.budget <= 0:
        print(f"table2text: --budget must be positive, got {args.budget}", file=sys.stderr)
        return 2

    try:
        ast = parse(args.file, sheet=args.sheet)
    except OSError as exc:
        print(f"table2text: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"table2text: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(ast.to_json(indent=1))
        return 0

    floor = floor_tokens(ast)
    if args.budget < floor:
        print(
            f"table2text: budget {args.budget} is below this file's "
            f"structural floor ({floor} tokens); emitting the floor brief — "
            "a complete description beats a truncated one",
            file=sys.stderr,
        )
    out = brief_with_facts(ast, budget=args.budget)
    named = {f[1:3] for f in out.facts if f[0] == "col_name"}
    total = sum(len(t.stats.columns) for t in ast.tables)
    if len(named) < total and _wide(ast):
        best = packed_best(ast)
        best_named = len({f[1:3] for f in best.facts if f[0] == "col_name"})
        if best_named > len(named):
            reach = (
                f"--budget {count_tokens(best.text)} names {best_named}"
                if best_named < total
                else f"--budget {count_tokens(best.text)} names all {total}"
            )
            print(
                f"table2text: {total - len(named)} of {total} column names "
                f"omitted at this budget; {reach}; --json is lossless",
                file=sys.stderr,
            )
        else:
            print(
                f"table2text: {total - len(named)} of {total} column names "
                "omitted (line-guard bound for this file); --json is lossless",
                file=sys.stderr,
            )
    print(out.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
