"""Reading and appending session records.

WRITTEN TO FILL A GAP, 2026-09-20. app.py uses four functions:
load_json, load_jsonl, append_jsonl and find_session.

JSONL, not a database, because the unit of work here is one immutable
session record written once and never updated -- appending a line is the
whole write path, and it survives being inspected or diffed by hand, which
matters for a record that is field evidence.

Reads are deliberately forgiving: a truncated final line (a process killed
mid-append) loses that one record instead of making the whole history
unreadable. Writes are not forgiving -- they create the parent directory and
flush, so a saved session is on disk before the redirect is issued.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

__all__ = ["load_json", "load_jsonl", "append_jsonl", "find_session"]


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Every record in the file. Missing file means no sessions yet, not an error."""
    file_path = Path(path)
    if not file_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with file_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # A partial trailing line from an interrupted append. Skip it
                # rather than lose every earlier session to one bad byte.
                continue
            if isinstance(record, dict):
                rows.append(record)
    return rows


def append_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, default=str)
    with file_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def find_session(sessions: Iterable[dict[str, Any]],
                 session_id: str) -> dict[str, Any] | None:
    for session in sessions:
        if session.get("session_id") == session_id:
            return session
    return None
