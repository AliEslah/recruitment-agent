# Documentation Cleanup Report

Date: 2026-06-23

## Scope

Prepared the repository documentation for public GitHub release under `AGPL-3.0-only`.

## Public User Docs

- `README.md`
- `docs/getting-started.md`
- `docs/local-llm.md`
- `docs/frontend.md`
- `docs/evaluation.md`
- `docs/limitations.md`
- `frontend/README.md`
- `evals/README.md`

## Public Reference Docs

- `docs/README.md`
- `docs/architecture.md`
- `docs/backend.md`
- `docs/security.md`
- `docs/deployment.md`
- `docs/pilot.md`
- `docs/roadmap.md`
- `docs/commercial.md`
- `docs/development-workflow.md`
- `docs/LICENSE_DECISION.md`
- `frontend/docs/DEPENDENCY_AUDIT.md`
- `COMMERCIAL.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `.github/`

## Archived Historical Docs

Historical phase notes, audits, and QA reports were moved under `docs/archive/` and indexed in `docs/archive/README.md`. They are retained for maintainer context and are not the primary public setup docs.

## Evaluation Reports

The public tracked eval report set was reduced to the final synthetic 42-of-42 report:

- `evals/reports/final_42_of_42_eval_report.md`
- `evals/reports/final_42_of_42_eval_report.json`

Timestamped generated reports are ignored by default.

## Hygiene Scan Results

- No root or nested `.env` file found.
- No `node_modules`, `.next`, caches, logs, or runtime upload directories left in the cleaned tree.
- No private local home-directory paths found in repository files.
- No internal assistant conversation artifacts found.
- No raw `sk-`, GitHub, AWS, Slack, JWT-shaped, or cloud LLM API tokens found.
- OTP literal scan found no committed numeric OTP values.
- `JWT_SECRET_KEY` hits are limited to local placeholder examples, tests, and historical scan notes.
- Eval fixtures and selected reports are synthetic-only.

## Validation Results

Passed:

```bash
uv run pytest -q
uv run ruff check backend/app tests
uv run alembic upgrade head
uv run python -m app.scripts.run_evals --dry-run-fixtures
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

Notes:

- `uv run pytest -q` passed 93 tests with one third-party FastAPI/Starlette testclient deprecation warning.
- `npm install` was run because `frontend/node_modules` was absent. It reported 3 npm audit vulnerabilities in the current dependency graph: 1 low and 2 moderate. The dependency audit doc remains in `frontend/docs/DEPENDENCY_AUDIT.md`.
- Generated validation artifacts were removed after the checks.

## Remaining Public-Release Blockers

No documentation, licensing, or repository-hygiene blockers remain from this cleanup pass.
