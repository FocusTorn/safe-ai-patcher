"""Core transaction engine for Safe AI Patcher."""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .history import record_transaction
from .project import detect_git, git_changed_paths


class PatchError(Exception):
    """Raised when a patch cannot be safely applied."""


@dataclass(frozen=True)
class Change:
    path: str
    content: str


@dataclass
class Snapshot:
    path: Path
    existed: bool
    content: bytes | None
    mode: int | None


def _safe_path(root: Path, relative: str) -> Path:
    """Resolve a patch path and reject paths outside the project."""
    if not relative or Path(relative).is_absolute():
        raise PatchError(f"Unsafe path: {relative!r}")

    candidate = (root / relative).resolve()
    root = root.resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PatchError(f"Unsafe path outside project: {relative!r}") from exc

    return candidate


def _snapshot(root: Path, changes: list[Change]) -> list[Snapshot]:
    snapshots = []

    for change in changes:
        path = _safe_path(root, change.path)

        if path.exists():
            if not path.is_file():
                raise PatchError(f"Not a regular file: {change.path}")

            snapshots.append(
                Snapshot(
                    path=path,
                    existed=True,
                    content=path.read_bytes(),
                    mode=path.stat().st_mode,
                )
            )
        else:
            snapshots.append(
                Snapshot(
                    path=path,
                    existed=False,
                    content=None,
                    mode=None,
                )
            )

    return snapshots


def _atomic_write(path: Path, content: str, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".sap-tmp",
        dir=path.parent,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        if mode is not None:
            os.chmod(temp_name, mode)

        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def _rollback(snapshots: list[Snapshot]) -> None:
    for snapshot in snapshots:
        if snapshot.existed:
            assert snapshot.content is not None

            snapshot.path.parent.mkdir(parents=True, exist_ok=True)

            fd, temp_name = tempfile.mkstemp(
                prefix=f".{snapshot.path.name}.",
                suffix=".sap-rollback",
                dir=snapshot.path.parent,
            )

            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(snapshot.content)
                    handle.flush()
                    os.fsync(handle.fileno())

                if snapshot.mode is not None:
                    os.chmod(temp_name, snapshot.mode)

                os.replace(temp_name, snapshot.path)
            except Exception:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass
                raise
        elif snapshot.path.exists():
            snapshot.path.unlink()


def apply_changes(
    root: str | Path,
    changes: list[Change],
    test_command: list[str] | None = None,
    allow_dirty: bool = False,
) -> None:
    """Apply changes as one transaction.

    If validation, writing, or testing fails, all changes are rolled back.
    """
    root = Path(root).resolve()

    if not root.is_dir():
        raise PatchError(f"Project root does not exist: {root}")

    if not changes:
        raise PatchError("No changes supplied")

    # Validate every path before touching anything.
    paths = [_safe_path(root, change.path) for change in changes]

    if len(paths) != len(set(paths)):
        raise PatchError("Duplicate paths in change set")

    if not allow_dirty:
        git = detect_git(root)

        if git.available:
            changed_paths = git_changed_paths(git.root)
            patch_paths = {change.path for change in changes}

            conflicts = sorted(changed_paths & patch_paths)

            if conflicts:
                raise PatchError(
                    "Git worktree has uncommitted changes in: "
                    + ", ".join(conflicts)
                    + " (use allow_dirty=True to override)"
                )

    snapshots = _snapshot(root, changes)

    try:
        for change, snapshot in zip(changes, snapshots):
            _atomic_write(snapshot.path, change.content, snapshot.mode)

        if test_command:
            result = subprocess.run(
                test_command,
                cwd=root,
                check=False,
            )

            if result.returncode != 0:
                raise PatchError(
                    f"Test command failed with exit code {result.returncode}"
                )

    except Exception as exc:
        _rollback(snapshots)
        record_transaction(
            root,
            status="rolled_back",
            paths=[change.path for change in changes],
            test_command=test_command,
            error=str(exc),
        )
        raise
    else:
        record_transaction(
            root,
            status="committed",
            paths=[change.path for change in changes],
            test_command=test_command,
        )
