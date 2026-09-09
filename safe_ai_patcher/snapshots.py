"""Persistent transaction snapshots for Safe AI Patcher."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import uuid4

from .core import Change, PatchError, _safe_path, _snapshot


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def create_snapshot(root: str | Path, changes: list[Change]) -> str:
    """Persist pre-transaction state plus expected post-transaction state."""
    root = Path(root).resolve()
    transaction_id = uuid4().hex
    directory = root / ".sap" / "transactions" / transaction_id
    directory.mkdir(parents=True, exist_ok=False)

    snapshots = _snapshot(root, changes)
    metadata = []

    for index, (snapshot, change) in enumerate(zip(snapshots, changes)):
        entry = {
            "path": str(snapshot.path.relative_to(root)),
            "existed": snapshot.existed,
            "mode": snapshot.mode,
            "expected_exists": True,
            "expected_hash": _hash_bytes(change.content.encode("utf-8")),
        }

        if snapshot.existed:
            data = snapshot.content
            filename = f"{index}.bin"
            (directory / filename).write_bytes(data)
            entry["file"] = filename

        metadata.append(entry)

    (directory / "metadata.json").write_text(
        json.dumps({"paths": metadata}, indent=2),
        encoding="utf-8",
    )

    return transaction_id


def _current_matches_expected(root: Path, entry: dict) -> bool:
    target = _safe_path(root, entry["path"])

    if not target.exists():
        return False

    if not target.is_file():
        return False

    return _hash_bytes(target.read_bytes()) == entry["expected_hash"]


def restore_snapshot(
    root: str | Path,
    transaction_id: str,
    *,
    force: bool = False,
) -> list[str]:
    """Restore a persistent transaction snapshot safely."""
    root = Path(root).resolve()
    directory = root / ".sap" / "transactions" / transaction_id
    metadata_path = directory / "metadata.json"

    if not metadata_path.is_file():
        raise PatchError(f"Transaction snapshot not found: {transaction_id}")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PatchError(
            f"Invalid transaction snapshot: {transaction_id}"
        ) from exc

    entries = metadata.get("paths", [])

    if not force:
        conflicts = [
            entry["path"]
            for entry in entries
            if not _current_matches_expected(root, entry)
        ]
        if conflicts:
            paths = ", ".join(conflicts)
            raise PatchError(
                "Rollback refused: files changed after the transaction: "
                f"{paths}. Use --force to override."
            )

    restored = []

    for entry in entries:
        target = _safe_path(root, entry["path"])

        if entry["existed"]:
            data = (directory / entry["file"]).read_bytes()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(entry["mode"])
        elif target.exists():
            if target.is_dir():
                raise PatchError(f"Cannot remove directory: {entry['path']}")
            target.unlink()

        restored.append(entry["path"])

    return restored


def cleanup_snapshots(
    root: str | Path,
    keep: int = 10,
) -> list[str]:
    """Remove old transaction snapshots while preserving rollback targets."""
    if keep < 0:
        raise ValueError("keep must be non-negative")

    root = Path(root).resolve()
    transactions = root / ".sap" / "transactions"

    if not transactions.is_dir():
        return []

    from .history import load_history

    protected = {
        record["rollback_of"]
        for record in load_history(root)
        if record.get("rollback_of")
    }

    directories = [
        path
        for path in transactions.iterdir()
        if path.is_dir() and (path / "metadata.json").is_file()
    ]
    directories.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    removable = [
        path
        for path in directories[keep:]
        if path.name not in protected
    ]

    removed = []

    for directory in removable:
        for child in directory.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
        directory.rmdir()
        removed.append(directory.name)

    return removed


def cleanup_snapshots(
    root: str | Path,
    keep: int = 10,
) -> list[str]:
    """Remove old transaction snapshots while preserving rollback targets."""
    if keep < 0:
        raise ValueError("keep must be non-negative")

    root = Path(root).resolve()
    transactions = root / ".sap" / "transactions"

    if not transactions.is_dir():
        return []

    from .history import load_history

    protected = {
        record["rollback_of"]
        for record in load_history(root)
        if record.get("rollback_of")
    }

    directories = [
        path
        for path in transactions.iterdir()
        if path.is_dir() and (path / "metadata.json").is_file()
    ]
    directories.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    removable = [
        path
        for path in directories[keep:]
        if path.name not in protected
    ]

    removed = []

    for directory in removable:
        for child in directory.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
        directory.rmdir()
        removed.append(directory.name)

    return removed
