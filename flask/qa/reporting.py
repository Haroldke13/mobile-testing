from __future__ import annotations

import csv
import io
from collections import Counter
from datetime import datetime
from typing import Iterable

SEVERITY_ORDER = {"S1": 0, "S2": 1, "S3": 2, "S4": 3}


def session_duration_minutes(session: dict) -> float:
    start = datetime.fromisoformat(session["started_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(session["ended_at"].replace("Z", "+00:00"))
    return round((end - start).total_seconds() / 60, 1)


def build_summary(sessions: Iterable[dict]) -> dict:
    rows = list(sessions)
    statuses = Counter()
    severities = Counter()
    categories = Counter()
    total_issues = 0
    observed_sessions = 0
    synthetic_sessions = 0
    durations: list[float] = []

    for session in rows:
        if session.get("source") == "observed":
            observed_sessions += 1
        elif session.get("source") == "synthetic_demo":
            synthetic_sessions += 1
        durations.append(session_duration_minutes(session))
        for result in session.get("test_results", []):
            statuses[result.get("status", "UNKNOWN")] += 1
        for issue in session.get("issues", []):
            total_issues += 1
            severities[issue.get("severity", "UNKNOWN")] += 1
            categories[issue.get("category", "UNKNOWN")] += 1

    executed = statuses["PASS"] + statuses["FAIL"] + statuses["BLOCKED"]
    pass_rate = round((statuses["PASS"] / executed) * 100, 1) if executed else 0.0
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0.0
    return {
        "sessions": len(rows),
        "observed_sessions": observed_sessions,
        "synthetic_sessions": synthetic_sessions,
        "test_status_counts": dict(statuses),
        "total_issues": total_issues,
        "severity_counts": dict(severities),
        "category_counts": dict(categories),
        "pass_rate": pass_rate,
        "average_duration_minutes": avg_duration,
    }


def render_markdown_report(session: dict, cases_by_id: dict[str, dict[str, str]]) -> str:
    source_note = (
        "Observed manual test session." if session["source"] == "observed"
        else "SYNTHETIC DEMO DATA — this is not a claim about the client's application."
    )
    lines = [
        f"# Android QA Session Report — {session['session_id']}",
        "",
        f"> {source_note}",
        "",
        "## Session metadata",
        "",
        f"- Device: {session['device']['model']}",
        f"- Android: {session['device']['android_version']}",
        f"- Network: {session['device']['network']}",
        f"- Location: {session['location']}",
        f"- Started: {session['started_at']}",
        f"- Ended: {session['ended_at']}",
        f"- Duration: {session_duration_minutes(session)} minutes",
        "",
        "## Test execution",
        "",
        "| Case | Area | Test | Status | Notes |",
        "|---|---|---|---|---|",
    ]
    for result in session["test_results"]:
        case = cases_by_id.get(result["case_id"], {})
        notes = result.get("notes", "").replace("|", r"\|").replace("\n", " ")
        lines.append(
            f"| {result['case_id']} | {case.get('area', 'Unknown')} | "
            f"{case.get('title', 'Unknown test')} | {result['status']} | {notes} |"
        )
    lines.extend(["", "## Issues", ""])
    if not session.get("issues"):
        lines.append("No issues recorded in this session.")
    else:
        for issue in sorted(session["issues"], key=lambda i: SEVERITY_ORDER.get(i["severity"], 99)):
            lines.extend([
                f"### {issue['issue_id']} — {issue['title']}",
                "",
                f"- Area: {issue['area']}",
                f"- Category: {issue['category']}",
                f"- Severity / Priority: {issue['severity']} / {issue['priority']}",
                f"- Reproducibility: {issue['reproducibility']}",
                f"- Expected: {issue['expected']}",
                f"- Actual: {issue['actual']}",
                f"- Evidence: {issue.get('evidence_ref') or 'Not attached'}",
                "",
                "Reproduction steps:",
            ])
            for number, step in enumerate(issue["steps"], start=1):
                lines.append(f"{number}. {step}")
            lines.append("")
    lines.extend([
        "## Quality note",
        "",
        "This report distinguishes observed sessions from synthetic demo data. A FAIL requires notes and an issue record; defect records carry reproduction steps, expected vs actual behavior, severity, priority, and evidence reference.",
        "",
    ])
    return "\n".join(lines)


def render_issue_csv(session: dict) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "session_id", "source", "issue_id", "area", "category", "title", "severity",
        "priority", "reproducibility", "expected", "actual", "steps", "evidence_ref"
    ])
    writer.writeheader()
    for issue in session.get("issues", []):
        writer.writerow({
            "session_id": session["session_id"],
            "source": session["source"],
            "issue_id": issue["issue_id"],
            "area": issue["area"],
            "category": issue["category"],
            "title": issue["title"],
            "severity": issue["severity"],
            "priority": issue["priority"],
            "reproducibility": issue["reproducibility"],
            "expected": issue["expected"],
            "actual": issue["actual"],
            "steps": " > ".join(issue["steps"]),
            "evidence_ref": issue.get("evidence_ref", ""),
        })
    return output.getvalue()


def render_short_feedback(session: dict) -> str:
    counts = Counter(result["status"] for result in session.get("test_results", []))
    source = "Observed session" if session["source"] == "observed" else "SYNTHETIC DEMO — not client-app evidence"
    lines = [
        f"Android App Test Feedback — {session['session_id']}",
        source,
        f"Device: {session['device']['model']} / Android {session['device']['android_version']}",
        f"Location: {session['location']} | Network: {session['device']['network']}",
        f"Duration: {session_duration_minutes(session)} minutes",
        f"Results: {counts['PASS']} PASS, {counts['FAIL']} FAIL, {counts['BLOCKED']} BLOCKED, {counts['NOT_RUN']} NOT RUN",
        "",
        "Findings:",
    ]
    if session.get("issues"):
        for issue in sorted(session["issues"], key=lambda i: SEVERITY_ORDER.get(i["severity"], 99)):
            lines.append(f"- [{issue['severity']}/{issue['priority']}] {issue['area']}: {issue['title']} ({issue['reproducibility']})")
    else:
        lines.append("- No defects were recorded in this session.")
    lines.extend([
        "",
        "Coverage: Home, start-application flow, FAQ/Help, Support/Contact, broken-link checks, usability observations, and obvious responsiveness blockers where reachable.",
    ])
    return "\n".join(lines) + "\n"