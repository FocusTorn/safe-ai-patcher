"""Persistent transaction history for Safe AI Patcher."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def record_transaction(
    root: str | Path,
    *,
    status: str,
    paths: list[str],
    test_command: list[str] | None = None,
    error: str | None = None,
    transaction_id: str | None = None,
    rollback_of: str | None = None,
    changes_count: int | None = None,
    duration: float | None = None,
    version: str = "0.2.0",
) -> str:
    """Append a transaction record to .sap/history.jsonl."""
    root = Path(root).resolve()
    history_dir = root / ".sap"
    history_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "id": transaction_id or uuid4().hex,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "paths": paths,
        "test_command": test_command,
    }

    if changes_count is not None:
        record["changes_count"] = changes_count

    if duration is not None:
        record["duration"] = duration

    if version is not None:
        record["version"] = version

    if error is not None:
        record["error"] = error

    if rollback_of is not None:
        record["rollback_of"] = rollback_of

    with (history_dir / "history.jsonl").open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")

    return record["id"]


def load_transaction(
    root: str | Path,
    transaction_id: str,
) -> dict | None:
    """Load one transaction by its full ID."""
    for record in load_history(root):
        if record.get("id") == transaction_id:
            return record
    return None


def load_history(
    root: str | Path,
    limit: int | None = None,
) -> list[dict]:
    """Load transaction history, newest first."""
    history = Path(root).resolve() / ".sap" / "history.jsonl"

    if not history.is_file():
        return []

    records = []

    for line in history.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))

    records.reverse()

    if limit is not None:
        records = records[:limit]

    return records
