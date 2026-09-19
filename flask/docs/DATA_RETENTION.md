# QA Evidence Retention and Privacy

This project does not need sensitive personal data to perform the stated mobile QA work. Record only the device model, Android version, broad test location (city/country), network type, timestamps, test outcomes and defect evidence references.

## Safeguards
- Do not enter real personal, financial or account information into test flows unless the client explicitly provides approved test credentials/data.
- Prefer redacted screenshots. Avoid notification banners, contacts, phone numbers, email addresses or other unrelated personal content in evidence.
- Keep raw screen recordings only as long as needed for client review. A practical default is deletion after acceptance or 30 days, whichever comes first, unless the client requires another period.
- Do not commit client screenshots, recordings, credentials or Play Store access tokens to Git.
- `data/sessions.jsonl` is gitignored so observed session records remain local unless intentionally exported.
- Synthetic demo data is permanently labeled `synthetic_demo` and cannot be mistaken for observed evidence in generated reports.