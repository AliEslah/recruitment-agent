# Development Workflow

Use the validation cadence. Do not run full verification after every small task.

## Check Levels

| When | Command | What It Runs |
| --- | --- | --- |
| Small backend-only task | `uv run python scripts/check_backend_fast.py` | Ruff plus unit tests only |
| Small frontend-only task | `cd frontend && npm run check:fast` | Typecheck, lint, frontend unit tests |
| Batch of 3-4 tasks or pre-commit checkpoint | `uv run python scripts/check_checkpoint.py` | Backend non-slow tests, Ruff, frontend typecheck/lint/tests |
| End of phase or major merge | `uv run python scripts/check_full.py` | Backend tests, Ruff, migrations, frontend typecheck/lint/tests/build |
| Prompt, schema, scoring, interview, scorecard, or eval-helper change | `uv run python scripts/check_eval_targeted.py --stage candidate_scoring` | LM Studio health plus selected real eval stages |
| AI quality milestone | `uv run python scripts/check_eval.py` | LM Studio health plus the full real eval suite |
| Pilot release | `uv run python scripts/check_full.py` plus `uv run python scripts/check_eval.py` plus an explicit browser flow | Full phase, real evals, and manual or Playwright browser validation |

This repo does not currently use Poe. If Poe is added later, keep aliases such as `check:backend-fast`, `check:checkpoint`, `check:full`, `check:eval-targeted`, and `check:eval` mapped to the same operations.

## Backend Checks

Fast backend check:

```bash
uv run python scripts/check_backend_fast.py
```

Equivalent operations:

```bash
uv run ruff check backend/app tests
uv run pytest -q -m "unit and not lmstudio and not e2e and not mailpit and not slow"
```

Backend full check:

```bash
uv run python scripts/check_backend_full.py
```

Equivalent operations:

```bash
uv run pytest -q
uv run ruff check backend/app tests
uv run alembic upgrade head
```

`uv run pytest -q` does not enable external or slow marked tests by default. Use the matching environment flag when you intentionally want one of those categories:

```bash
RUN_DB_TESTS=true uv run pytest -q -m db
RUN_MAILPIT_TESTS=true uv run pytest -q -m mailpit
RUN_LMSTUDIO_TESTS=true uv run pytest -q -m lmstudio
RUN_E2E=true uv run pytest -q -m e2e
RUN_SLOW_TESTS=true uv run pytest -q -m slow
```

## Frontend Checks

Fast frontend check:

```bash
cd frontend
npm run check:fast
```

Equivalent operations:

```bash
npm run typecheck
npm run lint
npm run test
```

Frontend build check:

```bash
cd frontend
npm run check:frontend-build
```

## Checkpoint And Full Checks

Checkpoint check:

```bash
uv run python scripts/check_checkpoint.py
```

Full phase check:

```bash
uv run python scripts/check_full.py
```

From `frontend/`, the same combined checks are available as:

```bash
npm run check:checkpoint
npm run check:full
```

## AI Eval Checks

Run real LM Studio evals only when prompts, structured output schemas, scoring logic, interview evaluation, final scorecard behavior, or eval quality helpers change.

Targeted eval check:

```bash
uv run python scripts/check_eval_targeted.py --stage candidate_scoring
uv run python scripts/check_eval_targeted.py --stage interview_evaluation
uv run python scripts/check_eval_targeted.py --stage final_scorecard
```

With no `--stage`, the targeted script runs `candidate_scoring`, `interview_evaluation`, and `final_scorecard`.

Full eval check:

```bash
uv run python scripts/check_eval.py
```

Both eval scripts run `uv run python -m app.scripts.check_lmstudio` first. They do not mock LLM output, fake eval results, bypass LM Studio, or call cloud LLM providers.

## Marker Discipline

Pytest uses strict markers. Unknown markers fail collection.

Use:

- `unit` for tests that require no external services.
- `db` for PostgreSQL-backed tests.
- `mailpit` for Mailpit-backed email tests.
- `lmstudio` for real local LM Studio tests.
- `e2e` for full local-stack or browser flows.
- `slow` for long-running tests that should not run in normal fast checks.

Any test that requires LM Studio, Mailpit, Docker services, full browser flow, real eval runner execution, or long-running LLM calls must carry one of the external or slow markers above. Unit tests may patch non-LLM helpers, but they must not introduce mock LLM output as a runtime substitute.
