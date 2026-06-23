# Next Steps

## Pilot Readiness

- Treat Phase 4B as operational verification, not evaluation-quality testing.
- Run the full backend and frontend checks before each pilot session.
- Keep LM Studio local and loaded with the configured model.
- Use `uv run python -m app.scripts.seed_pilot_data` for starter users, templates, question-bank items, draft jobs, and synthetic candidate inputs.
- Do not seed fake scores, fake interview evaluations, fake final scorecards, or fake LLM output.
- Use role templates only as editable job setup shortcuts.
- Run calibration, candidate processing, interview evaluation, and final scorecard generation through real LM Studio workflows.
- Do not run full or stage-specific LLM evals in Phase 4B. Use only `uv run python -m app.scripts.run_evals --dry-run-fixtures`.
- Use `uv run python -m app.scripts.check_lmstudio` only as a tiny health diagnostic.

## Pilot Setup

1. Confirm services in `docs/OPERATIONAL_CHECKLIST.md`.
2. Confirm pilot size in `docs/PILOT_RUNBOOK.md`.
3. Confirm candidate consent language with the pilot sponsor.
4. Run dry-run eval validation: `uv run python -m app.scripts.run_evals --dry-run-fixtures`.
5. Run `scripts/verify_pilot_readiness.sh`.
6. Seed pilot starter content.
7. Complete `docs/PILOT_MANUAL_VERIFICATION.md`.
8. Update `docs/PILOT_VERIFICATION_STATUS.md`.

## Feedback And Metrics

- Use the final scorecard feedback widget for recruiter and hiring-manager feedback.
- Use the candidate completion feedback widget for candidate interview feedback.
- Review admin feedback and pilot summary after each pilot session.
- Track time to shortlist, agreement with shortlist, scorecard trust, completion rate, manual corrections, unsupported evidence reports, rejected recommendations, and usefulness ratings.

## Not In Phase 4

- Production deployment hardening.
- Voice or video interviews.
- Coding assessment.
- LinkedIn or job board integrations.
- Full ATS replacement workflows.
- Automated final hiring decisions.
