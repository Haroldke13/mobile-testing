# Case Study — Turning a 10–15 Minute Android Test into Reproducible Evidence

## Problem
A client needs several Android testers to quickly explore core flows and provide concise feedback. The risk in this type of engagement is inconsistent reporting: one tester says “link broken,” another gives no reproduction steps, and demo/example data can accidentally be presented as a real finding.

## Approach
The implementation maps the brief to nine executable cases and enforces a small defect schema. A failed case needs notes and at least one issue record. Issues capture area, category, severity, priority, reproducibility, expected vs actual behavior, steps and an evidence reference. Session provenance is mandatory: `observed` or `synthetic_demo`.

The Flask layer allows a tester to enter the real device/session details, execute the checklist, save the record, inspect results and download short TXT feedback, detailed Markdown, and issue CSV. The repository also supports headless report generation from JSON fixtures.

## Demonstrated run
The included synthetic fixture contains **1 synthetic session**, **9 test-case results**, **1 synthetic defect**, and an **11.5-minute derived duration**. Eight of nine synthetic executed cases are PASS and one is FAIL, producing an 88.9% demo pass rate. These figures describe only the repository fixture; they are not measurements of the client's app.

## Quality controls
- Known test-case IDs only
- Duplicate case/issue IDs rejected
- End timestamp must follow start timestamp
- FAIL/BLOCKED requires notes
- FAIL requires an issue record
- Severity, priority and category constrained to documented values
- Synthetic and observed provenance remain visible in UI and exports

## Limits
The client app was not identified in the posting and no physical Android device is attached to this build environment. Therefore, the implementation validates the QA workflow and reporting system, not the client's product behavior. Real findings begin only when the client supplies the app and a tester executes the checklist on-device.