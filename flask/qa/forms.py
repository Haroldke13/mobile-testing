"""Turn the submitted HTML form into a session record.

WRITTEN TO FILL A GAP, 2026-09-20. app.py calls
`session_from_form(request.form, test_cases)` and passes the result straight
to `validate_session`.

DIVISION OF LABOUR, DELIBERATE
------------------------------
This module SHAPES, it does not judge. Every rule -- allowed statuses,
severities, the 5-minute floor on an observed session, "a FAIL requires an
issue" -- already lives in validation.py, and duplicating any of it here
would create two places to change and one of them would be missed. So this
only converts flat form keys into the nested structure, and lets
validate_session reject what is wrong. The one exception is the generated
session_id, which the form cannot supply.

FORM KEY SHAPE
--------------
    device_model, android_version, network, location,
    started_at, ended_at                      (datetime-local values)
    status-<CASE_ID>, notes-<CASE_ID>         one pair per catalogue case
    issue-<n>-area, -category, -title, -severity, -priority,
      -reproducibility, -expected, -actual, -steps, -evidence_ref

An issue block whose fields are all blank is dropped, so the form can offer
several and the tester fill none.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

__all__ = ["session_from_form", "ISSUE_BLOCKS", "new_session_id"]

ISSUE_BLOCKS = 3          # how many blank issue forms the page offers
_ISSUE_FIELDS = ("area", "category", "title", "severity", "priority",
                 "reproducibility", "expected", "actual", "evidence_ref")


def new_session_id(when: datetime | None = None) -> str:
    stamp = (when or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    return f"OBS-{stamp}-{uuid.uuid4().hex[:4].upper()}"


def _iso(value: str) -> str:
    """Pass a datetime-local value through as ISO-8601 with an offset.

    The browser sends '2026-09-20T14:05' with no timezone. Leaving it naive
    reaches validate_session, which parses it and compares two naive values
    successfully -- so it would work, and then compare wrongly the moment
    any other producer wrote an aware timestamp. Stamping UTC here keeps
    every record in the store comparable. Unparseable input is returned
    untouched so validation.py reports it, rather than this raising a
    different error from a different layer.
    """
    text = (value or "").strip()
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def session_from_form(form, test_cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    get = form.get

    results = []
    for case in test_cases:
        case_id = case["case_id"]
        status = (get(f"status-{case_id}") or "NOT_RUN").strip()
        results.append({
            "case_id": case_id,
            "status": status,
            "notes": (get(f"notes-{case_id}") or "").strip(),
        })

    issues = []
    for index in range(1, ISSUE_BLOCKS + 1):
        block = {field: (get(f"issue-{index}-{field}") or "").strip()
                 for field in _ISSUE_FIELDS}
        steps_raw = (get(f"issue-{index}-steps") or "").strip()
        steps = [line.strip() for line in re.split(r"[\r\n]+", steps_raw) if line.strip()]
        if not any(block.values()) and not steps:
            continue          # an untouched block is not an issue
        block["steps"] = steps
        block["issue_id"] = (get(f"issue-{index}-issue_id") or "").strip() \
            or f"BUG-{index:03d}"
        issues.append(block)

    return {
        "session_id": new_session_id(),
        "source": "observed",
        "device": {
            "model": (get("device_model") or "").strip(),
            "android_version": (get("android_version") or "").strip(),
            "network": (get("network") or "").strip(),
        },
        "location": (get("location") or "").strip(),
        "started_at": _iso(get("started_at")),
        "ended_at": _iso(get("ended_at")),
        "test_results": results,
        "issues": issues,
    }
