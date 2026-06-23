# AI Recruiting Decision Platform

[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL--3.0--only-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Local-first AI recruiting decision support for evidence-based screening and live chat interviews. The backend uses FastAPI, PostgreSQL, LangGraph, and LM Studio's local OpenAI-compatible API; the frontend is a Next.js App Router UI.

This project is licensed under the GNU Affero General Public License v3.0 only (`AGPL-3.0-only`). Commercial licensing, private deployment terms, managed hosting, and enterprise support are available from the maintainer; see [COMMERCIAL.md](COMMERCIAL.md).

## What It Does

- Creates jobs from raw job descriptions.
- Calibrates job descriptions into weighted hiring criteria with human approval.
- Uploads resumes and extracts text without an LLM.
- Parses, scores, and explains candidate fit with local LM Studio output.
- Supports human shortlist and final hiring decisions.
- Generates interview plans, secure invite emails, OTP checks, live interview turns, transcript evaluation, and final scorecards.
- Stores audit logs, communication logs, and LLM call logs with redaction boundaries.
- Provides a browser MVP for recruiter, manager, admin, and candidate interview flows.

## What It Does Not Do

- It is not an ATS replacement, legal compliance engine, automated hiring decision system, or production-hardened SaaS service.
- It does not scrape LinkedIn, integrate job boards, run coding assessments, or provide voice/video interviews.
- It does not call OpenAI cloud, Anthropic, Gemini, or another external LLM provider.
- It does not use mock LLM output, fake deterministic AI output, fake email success, or a cloud fallback.

## Safety And Hiring Disclaimer

This repository is decision-support software for local MVP exploration. AI-generated recommendations are advisory. Human reviewers own shortlist and final hiring decisions, and any deployment with real candidates must be reviewed for employment law, privacy, security, accessibility, retention, and bias requirements before use.

## Architecture

- Backend: FastAPI app under `backend/app`, with SQLAlchemy models, Alembic migrations, JWT/RBAC, SMTP email, file parsing, redaction, audit logs, and LangGraph workflows.
- LLM runtime: LM Studio on the local host. The `openai` SDK is used only as an OpenAI-compatible protocol client for LM Studio.
- Database: PostgreSQL through async SQLAlchemy and Alembic.
- Frontend: Next.js, TypeScript, Tailwind, React Query, and Vitest under `frontend/`.
- Local services: Docker Compose runs PostgreSQL, Mailpit, backend, and a one-shot migration service. LM Studio runs separately on the host.
- Evaluation: synthetic fixtures and report-only checks under `evals/`, using the same prompts and local LM Studio path as product code.

## Quick Start

Prerequisites: Python 3.11+, `uv`, Docker, Docker Compose, Node.js, npm, and LM Studio with `qwen/qwen3-4b-2507` loaded.

```bash
cp .env.example .env
docker compose up -d postgres mailpit
uv sync --dev
uv run alembic upgrade head
uv run python -m app.scripts.seed_dev_users
uv run uvicorn app.main:app --app-dir backend --reload
```

In another terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open:

- Frontend: [http://localhost:3000/login](http://localhost:3000/login)
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Mailpit: [http://localhost:8025](http://localhost:8025)
- LM Studio local API: [http://localhost:1234/v1](http://localhost:1234/v1)

Default local users are configured through `.env.example`:

- `recruiter@example.local`
- `manager@example.local`
- `admin@example.local`

Use the matching local passwords from your `.env` file. Change all secrets before any non-local deployment.

## Required Local Configuration

For a host-run backend:

```bash
LM_STUDIO_BASE_URL=http://localhost:1234/v1
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_ENABLE_THINKING=false
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
FRONTEND_BASE_URL=http://localhost:3000
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

For a Docker-run backend, set `LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1` because `localhost` inside the container is the backend container.

Health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/llm
uv run python -m app.scripts.check_lmstudio
```

## No-Mock AI Policy

The product path must use real local LM Studio calls for AI workflows. If LM Studio is unavailable, the system should fail clearly instead of fabricating a successful result.

Allowed:

- Synthetic eval fixtures.
- Human-authored expected eval notes.
- Cached outputs only when they were produced by the real LM Studio path.
- Unit-test doubles around non-LLM infrastructure.

Not allowed:

- Mock LLM output in runtime flows.
- Fake AI success paths.
- Fake email provider success in product flows.
- Cloud LLM fallback.
- Real candidate data in fixtures or reports.

## Evaluation

Fixture validation without LM Studio:

```bash
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

Real local-model evals:

```bash
uv run python -m app.scripts.check_lmstudio
uv run python -m app.scripts.run_evals --all
```

The public repository keeps a selected final synthetic report at [evals/reports/final_42_of_42_eval_report.md](evals/reports/final_42_of_42_eval_report.md). See [docs/evaluation.md](docs/evaluation.md).

## Validation

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

## Documentation

- [Docs index](docs/README.md)
- [Getting started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Local LM Studio](docs/local-llm.md)
- [Backend](docs/backend.md)
- [Frontend](docs/frontend.md)
- [Evaluation](docs/evaluation.md)
- [Security](docs/security.md)
- [Deployment](docs/deployment.md)
- [Pilot guidance](docs/pilot.md)
- [Limitations](docs/limitations.md)
- [Roadmap](docs/roadmap.md)
- [Commercial licensing](docs/commercial.md)
- [Development workflow](docs/development-workflow.md)

## License

This repository is released under `AGPL-3.0-only`; see [LICENSE](LICENSE). If you run a modified version as a network service, review the AGPL source-availability obligations before deployment.

Commercial licensing is available for private deployments, managed hosting, proprietary integrations, implementation help, and enterprise support. See [COMMERCIAL.md](COMMERCIAL.md).
