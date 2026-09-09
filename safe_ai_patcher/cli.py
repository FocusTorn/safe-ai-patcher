"""Command-line interface for Safe AI Patcher."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import Change, PatchError, apply_changes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sap",
        description="Safely apply AI-generated code changes.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser(
        "apply",
        help="Apply a file change as a transaction.",
    )
    apply_parser.add_argument(
        "file",
        help="File to change, relative to the project root.",
    )
    apply_parser.add_argument(
        "content",
        help="New file contents.",
    )
    apply_parser.add_argument(
        "--test",
        nargs="+",
        help="Command to run after applying the change.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "apply":
        root = Path.cwd()

        try:
            apply_changes(
                root,
                [Change(args.file, args.content)],
                test_command=args.test,
            )
        except PatchError as exc:
            print(f"sap: patch rejected: {exc}", file=sys.stderr)
            return 1

        print(f"Applied safely: {args.file}")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
