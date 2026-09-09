"""Command-line interface for Safe AI Patcher."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .changes import generate_diff, load_changes
from .history import load_history
from .core import PatchError, apply_changes
from .project import detect_git, detect_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sap",
        description="Safely apply AI-generated code changes.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_parser = subparsers.add_parser(
        "apply",
        help="Apply a structured change file as a transaction.",
    )
    apply_parser.add_argument(
        "change_file",
        help="JSON change file.",
    )
    apply_parser.add_argument(
        "--test",
        nargs="+",
        help="Command to run after applying the changes.",
    )
    apply_parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow applying over uncommitted changes to the same files.",
    )

    diff_parser = subparsers.add_parser(
        "diff",
        help="Preview a structured change file.",
    )
    diff_parser.add_argument(
        "change_file",
        help="JSON change file.",
    )

    history_parser = subparsers.add_parser(
        "history",
        help="Show transaction history.",
    )

    rollback_parser = subparsers.add_parser(
        "rollback",
        help="Restore a previous transaction snapshot.",
    )
    rollback_parser.add_argument(
        "transaction_id",
        help="Transaction ID to restore.",
    )
    rollback_parser.add_argument(
        "--force",
        action="store_true",
        help="Restore even if files changed after the transaction.",
    )
    history_parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Number of transactions to show.",
    )
    history_parser.add_argument(
        "--json",
        action="store_true",
        help="Output transaction history as JSON.",
    )

    subparsers.add_parser(
        "info",
        help="Show detected project and Git information.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "info":
        project = detect_project()
        git = detect_git(project.root)

        print(f"Project root: {project.root}")
        print(f"Project marker: {project.marker or 'none'}")

        if git.available:
            print(f"Git root: {git.root}")
            print(f"Git branch: {git.branch or 'detached/no branch'}")
            print(f"Git status: {'dirty' if git.dirty else 'clean'}")
        else:
            print("Git: not a repository")

        return 0

    if args.command == "rollback":
        from .history import record_transaction
        from .snapshots import restore_snapshot

        root = detect_project().root

        try:
            paths = restore_snapshot(
                root,
                args.transaction_id,
                force=args.force,
            )
        except PatchError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        try:
            record_transaction(
                root,
                status="rollback",
                paths=paths,
                rollback_of=args.transaction_id,
            )
        except OSError:
            pass

        print(
            f"Rolled back {args.transaction_id}: "
            f"{len(paths)} file(s)"
        )
        return 0

    if args.command == "history":
        root = detect_project().root

        if args.limit < 1:
            parser.error("history limit must be at least 1")

        records = load_history(root, args.limit)

        if args.json:
            import json

            print(json.dumps(records, indent=2))
            return 0

        if not records:
            print("No transaction history.")
            return 0

        for record in records:
            print(
                f"{record["timestamp"]} "
                f"{record["status"]} "
                f"{record["id"][:8]}"
            )

            for path in record["paths"]:
                print(f"  {path}")

            if record.get("test_command"):
                print(
                    "  test: "
                    + " ".join(record["test_command"])
                )

            if record.get("error"):
                print(f"  error: {record["error"]}")

        return 0

    if args.command == "diff":
        change_file = Path(args.change_file).resolve()
        root = detect_project(change_file.parent).root

        try:
            change_set = load_changes(change_file)
            diff = generate_diff(root, change_set.changes)
        except PatchError as exc:
            print(f"sap: patch rejected: {exc}", file=sys.stderr)
            return 1

        if diff:
            print(diff, end="")
        else:
            print("No changes.")

        return 0

    if args.command == "apply":
        change_file = Path(args.change_file).resolve()
        root = detect_project(change_file.parent).root

        try:
            change_set = load_changes(change_file)
            apply_changes(
                root,
                change_set.changes,
                test_command=args.test,
                allow_dirty=args.allow_dirty,
            )
        except PatchError as exc:
            print(f"sap: patch rejected: {exc}", file=sys.stderr)
            return 1

        print(f"Applied safely: {len(change_set.changes)} change(s)")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
