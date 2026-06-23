# Roadmap

This roadmap is scoped to improving the local-first MVP without changing the no-mock AI policy.

## Near Term

- Convert the initial Alembic migration from metadata-driven table creation to explicit `op.create_table` operations.
- Add CI-backed PostgreSQL migration checks.
- Broaden backend integration coverage for auth, candidate entry, email redaction, and admin logs.
- Add a stable browser E2E path when the local stack can run reliably in CI or a dedicated developer script.
- Tune eval score-band calibration and expand synthetic fixture coverage.

## Pilot Readiness

- Add rate limiting for candidate entry, OTP, uploads, and admin log endpoints.
- Define data retention and deletion procedures for uploads, transcripts, communication logs, audit logs, LLM logs, and eval reports.
- Document backup, restore, migration rollback, incident response, and secret rotation.
- Review accessibility, employment-law, privacy, and bias-risk requirements before real candidate use.
- Define deployment isolation and monitoring expectations for any managed or private deployment.

## Out Of Scope For The MVP

- Job board integrations.
- LinkedIn scraping.
- Full ATS sync.
- Voice and video interviews.
- Coding assessments.
- Automated final hiring decisions.
- Cloud LLM fallback.
