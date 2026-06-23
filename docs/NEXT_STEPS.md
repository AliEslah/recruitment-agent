# Next Steps

Recommended order after the Phase 3 evaluation-quality calibration pass:

## Validation Cadence

Do not run full verification after every small task. Use the cadence in [Development Workflow](DEVELOPMENT_WORKFLOW.md):

- Small backend task: `uv run python scripts/check_backend_fast.py`
- Small frontend task: `cd frontend && npm run check:fast`
- Batch of 3-4 tasks: `uv run python scripts/check_checkpoint.py`
- Phase complete: `uv run python scripts/check_full.py`
- AI quality change: `uv run python scripts/check_eval_targeted.py --stage <stage>`
- AI milestone: `uv run python scripts/check_eval.py`
- Pilot release: full check plus full eval plus explicit browser flow

## 1. Run And Tune Evaluation Quality

The Phase 3 eval framework now has synthetic role, resume, transcript, and expected-signal fixtures under `evals/`, prompt version constants, report-only quality checks, and a real-LM eval runner.

Next calibration loop:

1. Run `uv run python -m app.scripts.check_lmstudio`.
2. Run `uv run python -m app.scripts.run_evals --all`.
3. Review `evals/reports/*_eval_report.md`.
4. Tune prompts or schemas only from repeated evidence, missing-evidence, or consistency failures.
5. Keep all quality checks report-only until product owners decide what should block production flows.

Phase 3C-Lite latest real report: `evals/reports/20260623T111250Z_eval_report.md`.

Current quality follow-up:

- Tune score-band calibration so high scores with `POSSIBLE_MATCH` are not over-warned when missing evidence justifies caution.
- Reduce over-strong recommendations where fixture notes expect `POSSIBLE_MATCH`.
- Monitor empty risk lists on high-scoring candidate-score outputs.
- Make interview planning always include an explicit soft-skill question.

The eval suite is ready to support Phase 4 Pilot Readiness. Keep quality warnings report-only until pilot policy decides which checks should block production workflows.

## 2. Stabilize Database And Migrations

Remaining migration debt:

- Convert the initial `create_all()` migration to explicit Alembic operations.
- Keep migration execution as an explicit setup/deploy step in non-local environments.
- Add DB-backed migration/schema checks in CI once a test database is available.

## 3. Broaden Integration Tests

Add tests in this order:

1. Alembic upgrade from empty database in CI.
2. DB-backed repository tests for core entities and indexes.
3. Mailpit invite and OTP send flow.
4. LM Studio health integration test with `RUN_LMSTUDIO_TESTS=true`.
5. Eval runner integration test using real LM Studio and PostgreSQL, skipped unless explicitly enabled.
6. Full browser/API flow test using real LM Studio, skipped unless explicitly enabled with `RUN_E2E=true`.

Do not add mock LLM output as a runtime substitute. For pure unit tests, use deterministic fixtures only around non-LLM helpers.

## 4. Pilot Readiness

- Add operational runbooks for backup/restore, secret rotation, and migration rollback.
- Decide production auth provider integration instead of env-seeded local users.
- Add rate limits for candidate interview-entry endpoints.
- Add retention policy for communication logs, LLM logs, runtime uploads, eval reports, and failed raw LLM responses.

## 5. Product/UI Work

- Add Playwright E2E under an explicit `RUN_E2E=true` flow once the local backend, Mailpit, seeded users, and LM Studio can run reliably in CI or a dedicated developer script.
- Keep preserving the JWT, token/OTP, and client nonce boundaries.
- Keep final decisions human-owned; scorecards should stay evidence support, not automated hiring decisions.
- Add export/review workflows only after retention and audit policies are decided.
- Consider a broader recruiter interview search page after the candidate-detail interview list has enough production feedback.
- Keep voice/video interviews and coding assessments out of scope until the chat MVP is stable.

## 6. Dependency Follow-Up

- Re-run `npm audit` after compatible Vite/Vitest or Next releases are available.
- Do not use `npm audit fix --force`; the current Next/PostCSS advisory reports an invalid Next downgrade as its automated fix.
