# Getting Started

This guide starts the local MVP with PostgreSQL, Mailpit, FastAPI, Next.js, and LM Studio. It does not use cloud LLM providers or fake AI output.

## Prerequisites

- Python 3.11+
- `uv`
- Docker and Docker Compose
- Node.js and npm
- LM Studio with `qwen/qwen3-4b-2507` loaded

## Environment

Copy the backend template:

```bash
cp .env.example .env
```

The important local values are:

```bash
DATABASE_URL=postgresql+asyncpg://recruitment:recruitment@localhost:5432/recruitment
LM_STUDIO_BASE_URL=http://localhost:1234/v1
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_ENABLE_THINKING=false
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
SMTP_HOST=localhost
SMTP_PORT=1025
FRONTEND_BASE_URL=http://localhost:3000
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Use `LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1` when the backend runs inside Docker.

## Start Services

```bash
docker compose up -d postgres mailpit
uv sync --dev
uv run alembic upgrade head
uv run python -m app.scripts.seed_dev_users
uv run uvicorn app.main:app --app-dir backend --reload
```

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `frontend/.env.local`.

## URLs

- Frontend: [http://localhost:3000/login](http://localhost:3000/login)
- Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Mailpit UI: [http://localhost:8025](http://localhost:8025)
- LM Studio API: [http://localhost:1234/v1](http://localhost:1234/v1)

## Health Checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/llm
uv run python -m app.scripts.check_lmstudio
```

`/health/llm` must succeed before AI flows such as job calibration, candidate processing, interview evaluation, or final scorecard generation.

## Browser Flow

1. Log in as a seeded recruiter.
2. Create a job from the browser.
3. Run JD calibration and approve criteria.
4. Upload a synthetic or local test resume.
5. Process the candidate, review evidence, and submit a human shortlist decision.
6. Generate an interview plan and send an invite.
7. Use Mailpit to open the candidate link and retrieve the OTP.
8. Complete the candidate interview in the public candidate route.
9. Evaluate the interview, generate the final scorecard, and submit the final human decision.
10. Log in as admin to review LLM usage, audit logs, and redacted communication logs.

Do not use real candidate data in local fixtures, screenshots, issues, or public reports.
