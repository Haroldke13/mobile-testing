"""The test-case catalogue, read from CSV.

WRITTEN TO FILL A GAP, 2026-09-20. app.py calls load_test_cases(path) once
at startup and case_id_set(cases) to give validate_session the set of ids it
will accept.

CSV rather than code because the catalogue is the client's test plan, not
the application's logic -- it is edited by whoever runs the engagement, and
data/test_cases.csv already exists with the columns below.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

__all__ = ["load_test_cases", "case_id_set", "COLUMNS"]

COLUMNS = ("case_id", "area", "title", "steps", "expected")


def load_test_cases(path: str | Path) -> list[dict[str, Any]]:
    """Load the catalogue. An absent file yields an empty plan, not a crash.

    Returning [] rather than raising keeps the application startable on a
    fresh checkout: the pages render, the catalogue is visibly empty, and
    the cause is obvious. A startup exception here would look like the
    missing-module failure this app already had.
    """
    file_path = Path(path)
    if not file_path.exists():
        return []
    cases: list[dict[str, Any]] = []
    with file_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            case_id = (row.get("case_id") or "").strip()
            if not case_id:
                continue
            cases.append({column: (row.get(column) or "").strip()
                          for column in COLUMNS})
    return cases


def case_id_set(cases: Iterable[dict[str, Any]]) -> set[str]:
    return {case["case_id"] for case in cases if case.get("case_id")}
