"""Structured change-file loading and diff generation."""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass
from pathlib import Path

from .core import Change, PatchError, _safe_path


@dataclass(frozen=True)
class ChangeSet:
    changes: list[Change]


def load_changes(path: str | Path) -> ChangeSet:
    """Load and validate a JSON change file."""
    path = Path(path)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PatchError(f"Change file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PatchError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise PatchError("Change file must contain a JSON object")

    raw_changes = data.get("changes")

    if not isinstance(raw_changes, list) or not raw_changes:
        raise PatchError("Change file must contain a non-empty 'changes' list")

    changes = []

    for index, item in enumerate(raw_changes):
        if not isinstance(item, dict):
            raise PatchError(f"Change {index} must be an object")

        change_path = item.get("path")
        content = item.get("content")

        if not isinstance(change_path, str) or not change_path:
            raise PatchError(f"Change {index} has an invalid path")

        if not isinstance(content, str):
            raise PatchError(f"Change {index} has invalid content")

        changes.append(Change(change_path, content))

    return ChangeSet(changes)


def generate_diff(root: str | Path, changes: list[Change]) -> str:
    """Generate a unified diff without modifying files."""
    root = Path(root).resolve()
    output = []

    for change in changes:
        path = _safe_path(root, change.path)

        if path.exists():
            if not path.is_file():
                raise PatchError(f"Not a regular file: {change.path}")
            old = path.read_text(encoding="utf-8")
        else:
            old = ""

        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            change.content.splitlines(keepends=True),
            fromfile=f"a/{change.path}",
            tofile=f"b/{change.path}",
        )

        output.extend(diff)

    return "".join(output)
