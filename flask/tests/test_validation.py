from copy import deepcopy
from pathlib import Path

import pytest

from qa.storage import load_json
from qa.testcases import load_test_cases, case_id_set
from qa.validation import SessionValidationError, validate_session

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def demo():
    return load_json(ROOT / "data" / "demo_session.json")


@pytest.fixture
def case_ids():
    return case_id_set(load_test_cases(ROOT / "data" / "test_cases.csv"))


def test_demo_session_is_valid(demo, case_ids):
    assert validate_session(demo, case_ids)["session_id"] == "DEMO-ANDROID-001"


def test_end_time_must_follow_start(demo, case_ids):
    broken = deepcopy(demo)
    broken["ended_at"] = broken["started_at"]
    with pytest.raises(SessionValidationError, match="ended_at must be after started_at"):
        validate_session(broken, case_ids)


def test_failed_case_requires_issue(demo, case_ids):
    broken = deepcopy(demo)
    broken["issues"] = []
    with pytest.raises(SessionValidationError, match="failed test cases require"):
        validate_session(broken, case_ids)


def test_failed_case_requires_notes(demo, case_ids):
    broken = deepcopy(demo)
    failed = next(r for r in broken["test_results"] if r["status"] == "FAIL")
    failed["notes"] = ""
    with pytest.raises(SessionValidationError, match="requires notes"):
        validate_session(broken, case_ids)


def test_unknown_case_is_rejected(demo, case_ids):
    broken = deepcopy(demo)
    broken["test_results"][0]["case_id"] = "UNKNOWN-99"
    with pytest.raises(SessionValidationError, match="unknown case_id"):
        validate_session(broken, case_ids)


def test_duplicate_issue_id_is_rejected(demo, case_ids):
    broken = deepcopy(demo)
    broken["issues"].append(deepcopy(broken["issues"][0]))
    with pytest.raises(SessionValidationError, match="duplicate issue_id"):
        validate_session(broken, case_ids)


def test_observed_session_must_meet_minimum_duration(demo, case_ids):
    broken = deepcopy(demo)
    broken["source"] = "observed"
    broken["started_at"] = "2026-09-19T03:00:00+00:00"
    broken["ended_at"] = "2026-09-19T03:04:59+00:00"
    with pytest.raises(SessionValidationError, match="at least 5 minutes"):
        validate_session(broken, case_ids)