# Next Steps

Recommended order after the Phase 2C browser-flow recovery and backend UI contract pass:

## 1. Stabilize Database And Migrations

The P0 security blockers are fixed, and Phase 1B added the dedicated `migrate` Compose service, fresh-migration script, nonce binding, idempotency, indexes, status-transition helper, LLM usage logging, and P2 cleanup.

Remaining migration debt:

- Convert the initial `create_all()` migration to explicit Alembic operations.
- Keep migration execution as an explicit setup/deploy step in non-local environments.
- Add DB-backed migration/schema checks in CI once a test database is available.

## 2. Broaden Integration Tests

Add tests in this order:

1. Alembic upgrade from empty database in CI.
2. DB-backed repository tests for core entities and indexes.
3. Mailpit invite and OTP send flow.
4. LM Studio health integration test with `RUN_LMSTUDIO_TESTS=true`.
5. Full browser/API flow test using real LM Studio, skipped unless explicitly enabled with `RUN_E2E=true`.

Do not add mock LLM output as a runtime substitute. For pure unit tests, use deterministic fixtures only around non-LLM helpers.

## 3. Pilot Readiness

- Add operational runbooks for backup/restore, secret rotation, and migration rollback.
- Decide production auth provider integration instead of env-seeded local users.
- Add rate limits for candidate interview-entry endpoints.
- Add retention policy for communication logs, LLM logs, runtime uploads, and failed raw LLM responses.

## 4. Product/UI Work

- Add Playwright E2E under an explicit `RUN_E2E=true` flow once the local backend, Mailpit, seeded users, and LM Studio can run reliably in CI or a dedicated developer script.
- Keep preserving the JWT, token/OTP, and client nonce boundaries.
- Keep final decisions human-owned; scorecards should stay evidence support, not automated hiring decisions.
- Add export/review workflows only after retention and audit policies are decided.
- Consider a broader recruiter interview search page after the candidate-detail interview list has enough production feedback.
- Keep voice/video interviews and coding assessments out of scope until the chat MVP is stable.

## 5. Dependency Follow-Up

- Re-run `npm audit` after compatible Vite/Vitest or Next releases are available.
- Do not use `npm audit fix --force`; the current Next/PostCSS advisory reports an invalid Next downgrade as its automated fix.
