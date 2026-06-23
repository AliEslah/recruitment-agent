# Limitations

This repository is an MVP for local recruiting workflow exploration.

- AI recommendations are advisory and require human review.
- The project is not a legal compliance engine or automated hiring decision system.
- The backend is not production hardened.
- The initial Alembic migration still needs explicit table operations.
- Evaluation fixtures are synthetic and report-only; they are not a statistical validation suite.
- Evidence grounding uses simple heuristics and may miss valid paraphrases.
- Candidate interview recovery depends on browser session storage during an active interview.
- Playwright E2E is not configured yet.
- Voice/video interviews, coding assessments, ATS sync, LinkedIn scraping, and job board integrations are out of scope.
- The product path depends on LM Studio availability and does not fake successful AI output.
