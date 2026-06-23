# Contributing

Thanks for helping improve the AI Recruiting Decision Platform. This project is local-first and uses real LM Studio output for AI workflows, so changes should preserve that boundary.

## Local Setup

1. Install Python 3.11+, `uv`, Docker, Docker Compose, Node.js, and npm.
2. Review [docs/getting-started.md](docs/getting-started.md), then copy `.env.example` to `.env`.
3. Start PostgreSQL and Mailpit:

```bash
docker compose up -d postgres mailpit
```

4. Install backend dependencies and migrate:

```bash
uv sync --dev
uv run alembic upgrade head
```

5. Seed local development users if needed:

```bash
uv run python -m app.scripts.seed_dev_users
```

6. Install frontend dependencies:

```bash
cd frontend
npm install
cp .env.example .env.local
```

7. Start LM Studio locally with `qwen/qwen3-4b-2507` loaded before running AI flows or evals. See [docs/local-llm.md](docs/local-llm.md).

## Branches And Pull Requests

- Use focused branches and small PRs.
- Describe the behavior change, risk, and verification commands.
- Include screenshots only for UI changes.
- Do not include secrets, raw interview tokens, OTPs, real candidate data, runtime uploads, local databases, or private local paths.

## Coding Style

- Follow the existing FastAPI, SQLAlchemy, LangGraph, TypeScript, and Tailwind patterns.
- Keep changes scoped to the requested behavior.
- Do not add product features while doing cleanup or infrastructure work.
- Do not change prompts unless the change is needed for quality, safety, schema correctness, or removing private data.

## Checks

See [docs/development-workflow.md](docs/development-workflow.md) for the validation cadence.

Backend:

```bash
uv run pytest -q
uv run ruff check backend/app tests
uv run alembic upgrade head
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

For AI quality changes, run real LM Studio evals when LM Studio is available:

```bash
export RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
uv run python -m app.scripts.check_lmstudio
uv run python -m app.scripts.run_evals --all
```

Do not report fake pass results if LM Studio or another required service is unavailable.

## No-Mock AI Policy

- Do not add mock LLM output to runtime flows.
- Do not add fake AI success paths.
- Do not add cloud LLM fallback.
- Eval fixtures may be synthetic source inputs and human-authored expectations only.
- Cached outputs are acceptable only when they were produced by the real LM Studio path.

## Reporting Quality Issues

For model-quality issues, include:

- Commit SHA.
- LM Studio model id.
- Eval command or product flow.
- Relevant synthetic fixture or redacted reproduction.
- Generated report path when safe.
- Expected behavior and actual behavior.

Do not post real candidate data, raw tokens, OTPs, private resumes, or secrets.

## Adding Eval Fixtures

- Use synthetic people, emails, resumes, and transcripts.
- Label fixture intent clearly in file names and expected notes.
- Add expected signals under `evals/fixtures/expected/`.
- Run `uv run python -m app.scripts.run_evals --dry-run-fixtures`.
- Publish generated reports only after reviewing them for synthetic-only data.

## Adding Prompts Safely

- Version prompt changes with clear constants.
- Keep prompts grounded in provided source data.
- Avoid protected-attribute reasoning and unsupported claims.
- Keep local-only LM Studio behavior intact.
- Run targeted or full real evals for prompt changes when possible.
