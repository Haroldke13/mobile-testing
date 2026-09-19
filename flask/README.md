# Android Manual QA Evidence Kit

A compact, GitHub-ready toolkit for the Android manual-testing job described in the accompanying brief. It turns a 10–15 minute hands-on test into structured, reproducible evidence: required-flow test cases, validated session records, defect reports, CSV exports, and a Flask review interface.

**Important:** the repository includes only synthetic demo findings. No claim is made about the client's actual application because the posting did not include an app/package identifier, Play Store link or executable, and this environment has no physical Android test device.

## What it solves
The client wants reliable testers to install an Android app, explore Home, Start Application, FAQ/Help and Support/Contact, detect bugs/broken links/usability issues, and return concise written feedback. This repository provides the repeatable QA layer around that work rather than fabricating a client-app run.

## Architecture
- `data/test_cases.csv` — nine focused cases mapped to the posted flows.
- `qa/validation.py` — schema/quality gate for session results and defects.
- `qa/reporting.py` — derives duration, aggregate metrics, Markdown report and issue CSV.
- `qa/storage.py` — append-only local JSONL observed-session store.
- `app.py` — Flask application for capture, review and export.
- `data/demo_session.json` — explicitly synthetic fixture used for portfolio demonstration and tests.
- `scripts/` — repository validation and demo-output generation.
- `tests/` — validation, reporting, storage and Flask route tests.
- `docs/` — test plan, QA rubric, retention/privacy safeguards.
- `portfolio/` — client-safe project summary and handoff material.

## Prerequisites
- Python 3.10+
- pip
- For real execution: an Android device with internet access and the client's Play Store app.

## Install
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

The application reads environment variables directly. If your shell does not auto-load `.env`, export the values you need, for example:
```bash
export INCLUDE_DEMO_DATA=true
export QA_SESSION_FILE=data/sessions.jsonl
export SECRET_KEY='replace-for-production'
```

## Run the Flask app
```bash
python app.py
```
Then open `http://127.0.0.1:5000`. Use **New observed session** only after actually testing the client app.

### Empty-state / production mode
Disable the synthetic session when preparing a clean client workspace:
```bash
export INCLUDE_DEMO_DATA=false
python app.py
```

## Generate the included demo exports
```bash
python scripts/generate_demo_outputs.py
```
This writes:
- `outputs/demo_report.md`
- `outputs/demo_issues.csv`
- `outputs/demo_short_feedback.txt`

All demo outputs carry the `synthetic_demo` provenance.

## Run validation and tests
```bash
python scripts/validate_repository.py
pytest -q
python -m compileall -q app.py qa scripts tests
```

Expected local test behavior:
- Core validation/reporting/storage tests run with only pytest.
- Flask route tests require Flask and are skipped if it has not been installed.
- In a normal connected environment, `pip install -r requirements.txt` installs Flask and the route tests execute.

## Real testing workflow
1. Install the exact client app from Google Play.
2. Open the Flask form or use the CSV test plan as the checklist.
3. Record real device model, Android version, network, broad location and timestamps.
4. Execute the nine cases. Mark PASS/FAIL/BLOCKED/NOT_RUN.
5. For unexpected behavior, repeat safely to determine reproducibility.
6. Add an issue record with expected/actual result, severity, priority, steps and evidence reference.
7. Export short TXT feedback for submission, Markdown for detailed evidence, and CSV for structured triage.

## Input model
A session contains:
- `source`: `observed` or `synthetic_demo`
- device metadata
- broad location
- start/end timestamps
- one result per test case
- zero or more defect records

The validator rejects unknown test IDs, duplicate IDs, invalid statuses/severities/priorities, impossible timestamps, observed sessions shorter than five minutes, FAIL/BLOCKED cases without notes, and FAIL results without any issue record.

## Outputs
- Short plain-text client feedback
- Human-readable Markdown session report
- Machine-readable issue CSV
- Flask pages for aggregate metrics, session detail and capture
- Portfolio documentation and Mermaid architecture diagram

## Limitations
- This repository does not emulate or replace a physical Android device. The posted job specifically requires installation and hands-on use, so final client findings must come from a real Android session.
- No Play Store app name/link was supplied, so the client application could not be installed or tested here.
- The capture form provides one issue editor for speed; the persisted schema supports multiple issues and can be extended without changing report generation.
- Performance testing is deliberately observational only; this 10–15 minute manual brief does not justify instrumentation claims such as CPU, memory or network benchmarks.

## Deployment considerations
For a single tester, run locally. For team use, place the Flask app behind a production WSGI server, use authenticated access, replace JSONL with a transactional database, disable demo data, set a strong `SECRET_KEY`, and define the client's retention period before storing evidence.

## Skills genuinely exercised
- Mobile App Testing
- Manual Testing
- Functional Testing
- Usability Testing
- Android (device/test context and Android-specific capture metadata)

No Android application development is claimed: this deliverable tests an Android app and provides a Python/Flask QA evidence layer.