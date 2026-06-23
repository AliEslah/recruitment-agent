# Development Workflow

Use the smallest validation set that matches the change, then run the full release checks before publishing.

## Check Levels

| When | Command | What It Runs |
| --- | --- | --- |
| Backend-only task | `uv run python scripts/check_backend_fast.py` | Ruff plus unit tests |
| Frontend-only task | `cd frontend && npm run check:fast` | Typecheck, lint, frontend tests |
| Pre-commit checkpoint | `uv run python scripts/check_checkpoint.py` | Backend non-slow tests, Ruff, frontend typecheck/lint/tests |
| Major merge or release | `uv run python scripts/check_full.py` | Backend tests, Ruff, migrations, frontend typecheck/lint/tests/build |
| Prompt/schema/scoring change | `uv run python scripts/check_eval_targeted.py --stage candidate_scoring` | LM Studio health plus selected real eval stages |
| AI quality milestone | `uv run python scripts/check_eval.py` | LM Studio health plus full real eval suite |

## Public Release Checks

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

## Test Markers

Pytest uses strict markers:

- `unit`: no external services.
- `db`: PostgreSQL-backed tests.
- `mailpit`: Mailpit-backed email tests.
- `lmstudio`: real local LM Studio tests.
- `e2e`: full local-stack or browser flows.
- `slow`: long-running tests.

External and slow tests require explicit `RUN_*` flags. Unit tests may patch non-LLM helpers, but they must not introduce mock LLM output as a product substitute.

## AI Eval Discipline

Run real LM Studio evals after prompt, structured output schema, scoring, interview evaluation, final scorecard, or eval-helper changes. Do not report fake pass results if LM Studio or another required service is unavailable.
