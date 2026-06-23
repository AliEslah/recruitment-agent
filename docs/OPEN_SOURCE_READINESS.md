# Open-Source Readiness Report

Date: 2026-06-23

## Summary

The repository is cleaner and safer for public GitHub visibility. Public docs, contribution metadata, security guidance, GitHub templates, ignore rules, eval report policy, and dependency-audit notes have been added or updated.

Publication as a reusable open-source project is blocked until the maintainer chooses and adds a license.

## What Was Cleaned

- Removed disposable local cache/build artifacts from the source tree: `.pytest_cache`, source-tree `__pycache__` directories, `frontend/.next`, and `frontend/tsconfig.tsbuildinfo`.
- Expanded `.gitignore` for env files, frontend build output, Python caches, coverage, local databases, logs, runtime upload directories, local LLM failure output, Mailpit/runtime state, OS files, and editor folders.
- Moved intermediate eval reports to ignored local archive storage under `evals/reports/archive/`.
- Kept selected public-safe reports in `evals/reports/`:
  - `20260623T100907Z_eval_report.*`
  - `20260623T104144Z_eval_report.*`
  - `20260623T111250Z_eval_report.*`
- Rewrote selected eval report paths from an absolute local path to `evals`.
- Updated the eval report generator to write repo-relative `evals_root` values and a synthetic-data policy note.

## Files Added

- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `docs/LICENSE_DECISION.md`
- `docs/OPEN_SOURCE_READINESS.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/ISSUE_TEMPLATE/eval_quality_issue.md`
- `.github/PULL_REQUEST_TEMPLATE.md`

## Security Scan Summary

Scans run with git, dependency, build, and virtualenv directories excluded where appropriate.

- No `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY` values found.
- No macOS home-directory private local paths remain in source, docs, selected reports, or fixtures.
- `JWT_SECRET_KEY=` appears only in example/template/test files with local placeholder values.
- `REDACTED_INTERVIEW_TOKEN` and `REDACTED_OTP` appear only as redaction constants or documentation examples.
- `sk-` scan had a package-lock false positive inside an npm tarball URL, not a secret key.
- Selected eval reports and eval docs now state that fixtures are synthetic and must not contain real candidate data, raw tokens, OTPs, secrets, or private local paths.

## Dependency Audit Summary

Frontend audit:

- Command: `npm audit --json`
- Result: 1 low, 2 moderate, 0 high, 0 critical.
- Remaining advisories: transitive `esbuild`, nested `postcss` under `next`, and parent `next` advisory.
- No fix applied. `npm audit fix --dry-run --json` still points the Next/PostCSS path to an invalid semver-major downgrade to `next@9.3.3`.
- `npm view next version dependencies.postcss --json` shows latest `next@16.2.9` still declares `postcss 8.4.31`.

Backend dependency review:

- Command: `uv tree --depth 1`
- Result: reviewed declared backend dependencies.
- The `openai` SDK remains intentional because it is used as an OpenAI-compatible local client for LM Studio, not as a cloud fallback.
- No unused cloud-provider SDKs were added.

## Docs Status

Reviewed and updated public-facing docs:

- `README.md`
- `frontend/README.md`
- `evals/README.md`
- `docs/LM_STUDIO_SETTINGS.md`
- `docs/EVALUATION_QUALITY_PLAN.md`
- `docs/EVAL_TRIAGE_REPORT.md`
- `docs/NEXT_STEPS.md`
- `frontend/docs/DEPENDENCY_AUDIT.md`

Missing optional pilot docs:

- `docs/PILOT_LIMITATIONS.md`
- `docs/PILOT_RUNBOOK.md`
- `docs/OPERATIONAL_CHECKLIST.md`

Those files did not exist before this cleanup.

## License Status

No open-source license has been selected. `docs/LICENSE_DECISION.md` documents the maintainer decision needed before publication, and `README.md` warns readers not to reuse the code until a license is added.

## Verification Results

Passed:

- `uv run pytest -q`: 93 passed, 1 dependency deprecation warning.
- `uv run ruff check backend/app tests`: passed.
- `uv run alembic upgrade head`: passed against local PostgreSQL.
- `uv run python -m app.scripts.run_evals --dry-run-fixtures`: loaded 7 synthetic fixture sets.
- `RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507 uv run python -m app.scripts.check_lmstudio`: passed; tiny chat completion returned `{"ok": true}`.
- `RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507 uv run python -m app.scripts.run_evals --all`: passed, 42/42, summary score 1.0, 49 cache hits, 0 uncached calls.
- `cd frontend && npm run typecheck`: passed.
- `cd frontend && npm run lint`: passed.
- `cd frontend && npm run test`: passed, 7 tests.
- `cd frontend && npm run build`: passed.
- `docker compose up -d postgres mailpit backend`: services running.
- Backend health checks: `/health`, `/health/db`, and `/health/llm` returned 200.

Observed environment note:

- `uv run python -m app.scripts.check_lmstudio` without `RECRUITING_LLM_MODEL` failed as expected because the model env var is required.

## Commands Run

```bash
git status --short
git diff --stat
find . -name ".env" -o -name "*.log" -o -name "__pycache__" -o -name ".pytest_cache" -o -name ".next" -o -name "node_modules"
rg -n "sk-" .
rg -n "OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY" .
rg -n "JWT_SECRET_KEY=" .
rg -n "<macOS home-directory prefix>" .
rg -n "REDACTED_INTERVIEW_TOKEN|REDACTED_OTP" backend frontend docs
rg -n "localhost:3000|localhost:8000" docs README.md frontend backend evals
npm audit --json
npm ls esbuild postcss next --all
npm audit fix --dry-run --json
npm view next version dependencies.postcss --json
npm view vite@7 version dependencies.esbuild --json
npm view vitest@3 version dependencies.vite --json
uv tree --depth 1
uv run python -m pip list --format=columns
uv run pytest -q
uv run ruff check backend/app tests
uv run alembic upgrade head
uv run python -m app.scripts.run_evals --dry-run-fixtures
uv run python -m app.scripts.check_lmstudio
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507 uv run python -m app.scripts.check_lmstudio
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507 uv run python -m app.scripts.run_evals --all
cd frontend && npm run typecheck
cd frontend && npm run lint
cd frontend && npm run test
cd frontend && npm run build
docker compose ps
docker compose up -d postgres mailpit backend
curl -sS -i http://localhost:8000/health
curl -sS -i http://localhost:8000/health/db
curl -sS -i http://localhost:8000/health/llm
```

`uv run python -m pip list --format=columns` failed because this uv-managed environment does not install `pip` as a module. `uv tree --depth 1` was used for the backend dependency review.

## Remaining Known Limitations

- License is not selected.
- Frontend audit still has 1 low and 2 moderate advisories with no safe non-disruptive fix.
- Initial Alembic migration still uses `Base.metadata.create_all()`.
- Full production auth, retention, rate limiting, deployment hardening, and legal/compliance review remain out of scope for the MVP.
- Eval quality checks remain report-only and synthetic-fixture based.
- Playwright browser E2E is not configured.

## Publication Decision

Safe for public visibility after maintainer review: yes.

Safe to publish as reusable open source: no, not until a `LICENSE` file is added.

## Checklist Before Public GitHub Push

- [ ] Choose and add a `LICENSE` file.
- [x] Confirm no real secrets are committed.
- [x] Confirm no private local paths are committed.
- [x] Confirm no runtime data, uploads, logs, local DBs, or generated failure files are committed.
- [x] Confirm tests pass.
- [x] Confirm frontend builds.
- [x] Review dependency audit rationale.
- [x] Review docs and known limitations.
- [x] Keep no-mock/no-fake-output policy intact.
- [ ] Decide whether optional pilot runbooks should be added before publication.
