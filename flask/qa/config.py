"""Paths and environment handling.

WRITTEN TO FILL A GAP, 2026-09-20. app.py imports exactly three names --
DEMO_FILE, TEST_CASE_FILE, env_bool -- plus session_file().

session_file() is a function rather than a constant on purpose: app.py's
create_app() takes an optional session_path so a test can point the store at
a temporary file, and it falls back to this only when none is given. A
module-level constant would be resolved at import time and would make that
override useless in anything that imported the module first.
"""
from __future__ import annotations

import os
from pathlib import Path

__all__ = ["BASE_DIR", "DATA_DIR", "TEST_CASE_FILE", "DEMO_FILE",
           "env_bool", "session_file"]

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("QA_DATA_DIR", BASE_DIR / "data"))

TEST_CASE_FILE = DATA_DIR / "test_cases.csv"
DEMO_FILE = DATA_DIR / "demo_session.json"

_TRUE = {"1", "true", "yes", "on", "y"}
_FALSE = {"0", "false", "no", "off", "n"}


def env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean env var, tolerantly.

    Anything unrecognised returns the default rather than raising: a typo in
    an env var should not stop the application from starting.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    return default


def session_file() -> Path:
    """Where observed sessions are appended. Created on first write."""
    return Path(os.environ.get("QA_SESSION_FILE", DATA_DIR / "sessions.jsonl"))
