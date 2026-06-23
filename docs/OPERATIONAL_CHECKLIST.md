# Operational Checklist

## Phase 4B Verification Policy

Phase 4B is operational verification, not evaluation-quality testing. Do not run full LLM evals, stage-specific LLM evals, or expensive evaluation loops for this phase unless prompt text, prompt versions, LLM output schemas, evidence grounding logic, protected-term scanning, recommendation bands, or expected fixture behavior changed.

Allowed eval command for Phase 4B:

```bash
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

`uv run python -m app.scripts.check_lmstudio` is a tiny LM Studio health diagnostic only. It verifies configuration, `/models` reachability, and a small chat completion. It must not be treated as a recruiting workflow or quality evaluation.

Run the full operational verifier:

```bash
scripts/verify_pilot_readiness.sh
```

## Environment Variables

Required for local pilot:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `LM_STUDIO_BASE_URL`
- `RECRUITING_LLM_MODEL`
- `LM_STUDIO_API_KEY`
- `LM_STUDIO_ENABLE_THINKING=false`
- `RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false`
- `FRONTEND_BASE_URL`
- `CORS_ALLOW_ORIGINS`
- `SMTP_HOST`
- `SMTP_PORT`
- `EMAIL_FROM`
- `DEV_ADMIN_EMAIL`
- `DEV_ADMIN_PASSWORD`
- `DEV_RECRUITER_EMAIL`
- `DEV_RECRUITER_PASSWORD`
- `DEV_MANAGER_EMAIL`
- `DEV_MANAGER_PASSWORD`
- `PILOT_SEED_PASSWORD` if using `seed_pilot_data`

## Startup Commands

```bash
docker compose up -d postgres mailpit
uv sync --dev
uv run alembic upgrade head
export RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
export LM_STUDIO_BASE_URL=http://localhost:1234/v1
export LM_STUDIO_API_KEY=lm-studio
uv run python -m app.scripts.check_lmstudio
uv run python -m app.scripts.run_evals --dry-run-fixtures
uv run python -m app.scripts.seed_dev_users
uv run python -m app.scripts.seed_pilot_data
docker compose up -d --build backend
uv run uvicorn app.main:app --app-dir backend --reload
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Migration Commands

```bash
uv run alembic upgrade head
uv run alembic current
```

## Seed Commands

```bash
uv run python -m app.scripts.seed_dev_users
PILOT_SEED_PASSWORD='replace-me' uv run python -m app.scripts.seed_pilot_data
```

The pilot seed script creates users, question-bank items, draft demo jobs, and candidate input records only. It does not create AI scores, interview evaluations, final scorecards, or fake LLM output.

## LM Studio Setup

- Open LM Studio.
- Load the configured model.
- Start the local server.
- Confirm the model id matches `RECRUITING_LLM_MODEL`.
- Disable thinking for structured JSON workflows.

## Model Setup

Recommended local configuration:

```bash
LM_STUDIO_BASE_URL=http://localhost:1234/v1
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_ENABLE_THINKING=false
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
```

For Docker-run backend:

```bash
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

## Health Checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/llm
uv run python -m app.scripts.check_lmstudio
```

## Mailpit Or SMTP Checks

- Mailpit UI: `http://localhost:8025`.
- Send an interview invite and confirm the token is redacted in communication logs.
- Send an OTP and confirm the OTP is redacted in communication logs.
- Confirm candidate receives the message through the configured local channel.

## Frontend Build

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

## Backend Tests

```bash
uv run pytest -q
uv run ruff check backend/app tests
```

## Eval Command

Phase 4B dry-run fixture validation:

```bash
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

Do not run these during Phase 4B verification:

```bash
uv run python -m app.scripts.run_evals --all
uv run python -m app.scripts.run_evals --stage candidate_scoring
uv run python -m app.scripts.run_evals --stage interview_evaluation
uv run python -m app.scripts.run_evals --stage final_scorecard
```

Full or targeted LLM evals belong to evaluation-quality work, not pilot operational verification.

## Backup Note

Before running a real pilot, take a PostgreSQL backup and store it in approved internal storage. Do not include raw candidate resumes or LLM failure payloads in shared artifacts unless the pilot sponsor has approved that handling.

## Known Failure Modes

- LM Studio model unloaded or model id mismatch.
- Thinking model emits hidden reasoning instead of final JSON.
- SMTP or Mailpit not reachable.
- Candidate token expired.
- Candidate browser nonce lost after interview start.
- PostgreSQL container restarted without persisted volume.
- Frontend points at the wrong backend URL.

## Docker Unavailable

If Docker is unavailable, do not mark pilot verification passed. Start Docker Desktop or the Docker daemon, then run:

```bash
docker compose up -d postgres mailpit
uv run alembic upgrade head
```

Record the blocker in `docs/PILOT_VERIFICATION_STATUS.md`.

## LM Studio Unreachable

If LM Studio is unreachable, do not fake success and do not run recruiting workflows. Open LM Studio, load the configured model, start the local server, and set:

```bash
export RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
export LM_STUDIO_BASE_URL=http://localhost:1234/v1
export LM_STUDIO_API_KEY=lm-studio
```

For a Docker-run backend, use:

```bash
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

## Reset Pilot Data

For a full local reset:

```bash
docker compose down
docker compose up -d postgres mailpit
uv run alembic upgrade head
uv run python -m app.scripts.seed_dev_users
uv run python -m app.scripts.seed_pilot_data
```

For a partial reset, delete only the specific jobs, candidates, interviews, and feedback records needed for the demo. Do not delete unrelated user data.

## Export Logs

- Admin UI: `/admin` for recent audit, communication, LLM, feedback, and pilot summary views.
- Database export: use `pg_dump` for approved internal backups.
- LLM failure files: inspect `backend/data/llm_failures/` locally; redact before sharing.

Do not build or operate a full production deployment in this phase.
