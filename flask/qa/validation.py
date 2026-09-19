from __future__ import annotations

from datetime import datetime
from typing import Any

ALLOWED_SOURCES = {"observed", "synthetic_demo"}
ALLOWED_CASE_STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
ALLOWED_SEVERITIES = {"S1", "S2", "S3", "S4"}
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}
ALLOWED_CATEGORIES = {"functional", "usability", "broken_link", "performance", "content", "other"}


class SessionValidationError(ValueError):
    pass


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SessionValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _parse_iso(value: Any, field: str) -> datetime:
    text = _nonempty_string(value, field)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SessionValidationError(f"{field} must be ISO-8601") from exc


def validate_session(session: dict[str, Any], known_case_ids: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(session, dict):
        raise SessionValidationError("session must be an object")

    _nonempty_string(session.get("session_id"), "session_id")
    source = _nonempty_string(session.get("source"), "source")
    if source not in ALLOWED_SOURCES:
        raise SessionValidationError(f"source must be one of {sorted(ALLOWED_SOURCES)}")

    device = session.get("device")
    if not isinstance(device, dict):
        raise SessionValidationError("device must be an object")
    _nonempty_string(device.get("model"), "device.model")
    _nonempty_string(device.get("android_version"), "device.android_version")
    _nonempty_string(device.get("network"), "device.network")

    _nonempty_string(session.get("location"), "location")
    started = _parse_iso(session.get("started_at"), "started_at")
    ended = _parse_iso(session.get("ended_at"), "ended_at")
    if ended <= started:
        raise SessionValidationError("ended_at must be after started_at")
    duration_minutes = (ended - started).total_seconds() / 60
    if duration_minutes <= 0 or duration_minutes > 240:
        raise SessionValidationError("session duration must be between 0 and 240 minutes")
    if source == "observed" and duration_minutes < 5:
        raise SessionValidationError("observed session must be at least 5 minutes")

    results = session.get("test_results")
    if not isinstance(results, list) or not results:
        raise SessionValidationError("test_results must be a non-empty list")
    seen_case_ids: set[str] = set()
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            raise SessionValidationError(f"test_results[{index}] must be an object")
        case_id = _nonempty_string(result.get("case_id"), f"test_results[{index}].case_id")
        if case_id in seen_case_ids:
            raise SessionValidationError(f"duplicate case_id in test_results: {case_id}")
        seen_case_ids.add(case_id)
        if known_case_ids is not None and case_id not in known_case_ids:
            raise SessionValidationError(f"unknown case_id: {case_id}")
        status = _nonempty_string(result.get("status"), f"test_results[{index}].status")
        if status not in ALLOWED_CASE_STATUSES:
            raise SessionValidationError(f"invalid status for {case_id}: {status}")
        notes = result.get("notes", "")
        if not isinstance(notes, str):
            raise SessionValidationError(f"notes for {case_id} must be a string")
        if status in {"FAIL", "BLOCKED"} and not notes.strip():
            raise SessionValidationError(f"{case_id} requires notes when status is {status}")

    issues = session.get("issues", [])
    if not isinstance(issues, list):
        raise SessionValidationError("issues must be a list")
    issue_ids: set[str] = set()
    for index, issue in enumerate(issues):
        if not isinstance(issue, dict):
            raise SessionValidationError(f"issues[{index}] must be an object")
        issue_id = _nonempty_string(issue.get("issue_id"), f"issues[{index}].issue_id")
        if issue_id in issue_ids:
            raise SessionValidationError(f"duplicate issue_id: {issue_id}")
        issue_ids.add(issue_id)
        for field in ("area", "title", "expected", "actual", "reproducibility"):
            _nonempty_string(issue.get(field), f"issues[{index}].{field}")
        severity = _nonempty_string(issue.get("severity"), f"issues[{index}].severity")
        priority = _nonempty_string(issue.get("priority"), f"issues[{index}].priority")
        category = _nonempty_string(issue.get("category"), f"issues[{index}].category")
        if severity not in ALLOWED_SEVERITIES:
            raise SessionValidationError(f"invalid severity: {severity}")
        if priority not in ALLOWED_PRIORITIES:
            raise SessionValidationError(f"invalid priority: {priority}")
        if category not in ALLOWED_CATEGORIES:
            raise SessionValidationError(f"invalid category: {category}")
        steps = issue.get("steps")
        if not isinstance(steps, list) or not steps or not all(isinstance(s, str) and s.strip() for s in steps):
            raise SessionValidationError(f"issues[{index}].steps must be a non-empty list of strings")
        evidence_ref = issue.get("evidence_ref", "")
        if not isinstance(evidence_ref, str):
            raise SessionValidationError(f"issues[{index}].evidence_ref must be a string")

    failed_cases = {r["case_id"] for r in results if r["status"] == "FAIL"}
    if failed_cases and not issues:
        raise SessionValidationError("failed test cases require at least one issue record")

    return session