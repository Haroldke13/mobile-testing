from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, Response, abort, flash, redirect, render_template, request, url_for

from qa.config import DEMO_FILE, TEST_CASE_FILE, env_bool, session_file
from qa.forms import session_from_form
from qa.reporting import build_summary, render_issue_csv, render_markdown_report, render_short_feedback, session_duration_minutes
from qa.storage import append_jsonl, find_session, load_json, load_jsonl
from qa.testcases import load_test_cases, case_id_set
from qa.validation import SessionValidationError, validate_session


def create_app(session_path: Path | None = None, include_demo: bool | None = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")
    store_path = Path(session_path) if session_path else session_file()
    include_demo_data = env_bool("INCLUDE_DEMO_DATA", True) if include_demo is None else include_demo
    test_cases = load_test_cases(TEST_CASE_FILE)
    case_ids = case_id_set(test_cases)
    cases_by_id = {case["case_id"]: case for case in test_cases}

    def all_sessions() -> list[dict]:
        rows = load_jsonl(store_path)
        if include_demo_data and DEMO_FILE.exists():
            rows = [load_json(DEMO_FILE), *rows]
        return rows

    @app.template_filter("duration")
    def duration_filter(session: dict) -> float:
        return session_duration_minutes(session)

    @app.get("/")
    def index():
        sessions = all_sessions()
        return render_template("index.html", sessions=sessions, summary=build_summary(sessions))

    @app.get("/sessions/new")
    def new_session():
        return render_template("new_session.html", test_cases=test_cases)

    @app.post("/sessions")
    def create_session():
        session = session_from_form(request.form, test_cases)
        try:
            validate_session(session, case_ids)
        except SessionValidationError as exc:
            flash(str(exc), "error")
            return render_template("new_session.html", test_cases=test_cases, submitted=request.form), 400
        append_jsonl(store_path, session)
        flash("Observed session saved.", "success")
        return redirect(url_for("session_detail", session_id=session["session_id"]))

    @app.get("/sessions/<session_id>")
    def session_detail(session_id: str):
        session = find_session(all_sessions(), session_id)
        if session is None:
            abort(404)
        return render_template("session_detail.html", session=session, cases_by_id=cases_by_id)

    @app.get("/reports/<session_id>.md")
    def report_markdown(session_id: str):
        session = find_session(all_sessions(), session_id)
        if session is None:
            abort(404)
        body = render_markdown_report(session, cases_by_id)
        return Response(body, mimetype="text/markdown", headers={
            "Content-Disposition": f'attachment; filename="{session_id}.md"'
        })

    @app.get("/reports/<session_id>.csv")
    def report_csv(session_id: str):
        session = find_session(all_sessions(), session_id)
        if session is None:
            abort(404)
        body = render_issue_csv(session)
        return Response(body, mimetype="text/csv", headers={
            "Content-Disposition": f'attachment; filename="{session_id}-issues.csv"'
        })

    @app.get("/reports/<session_id>.txt")
    def report_short(session_id: str):
        session = find_session(all_sessions(), session_id)
        if session is None:
            abort(404)
        return Response(render_short_feedback(session), mimetype="text/plain", headers={
            "Content-Disposition": f'attachment; filename="{session_id}-feedback.txt"'
        })

    @app.get("/health")
    def health():
        return {"status": "ok", "test_cases": len(test_cases), "session_store": str(store_path)}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=env_bool("FLASK_DEBUG", False))