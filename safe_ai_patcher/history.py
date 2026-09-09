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
) -> None:
    """Append a transaction record to .sap/history.jsonl."""
    root = Path(root).resolve()
    history_dir = root / ".sap"
    history_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "id": uuid4().hex,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "paths": paths,
        "test_command": test_command,
    }

    if error is not None:
        record["error"] = error

    with (history_dir / "history.jsonl").open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
