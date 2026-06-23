# AI Recruiting Decision Platform

Backend-first MVP for an AI recruiting decision workflow. The app is FastAPI + PostgreSQL + LangGraph and uses LM Studio through its local OpenAI-compatible API. It does not call OpenAI cloud, Anthropic, Gemini, or any external LLM provider.

No open-source license has been selected yet. Do not reuse this code until a license is added.

## What This MVP Does

- Creates jobs from raw job descriptions.
- Uses `JobCalibrationGraph` to improve a JD and create weighted hiring criteria.
- Lets a human edit and approve criteria.
- Uploads candidate resumes and extracts PDF/text content without an LLM.
- Uses `CandidateProcessingGraph` to parse resumes and score candidates against approved criteria.
- Supports human shortlist decisions.
- Uses `InterviewPlanningGraph` to create a chat interview plan.
- Sends secure interview invites and OTPs through real SMTP, with Mailpit for local testing.
- Uses `LiveInterviewGraph` turn by turn for chat interviews.
- Uses `InterviewEvaluationGraph` and `FinalDecisionGraph` to produce evidence-based evaluations and scorecards.
- Stores audit logs, communication logs, and LLM call logs.

## Current Scope And Exclusions

- Frontend UI Alpha is available under `frontend/`.
- No coding assessment.
- No full ATS features.
- No LinkedIn scraping.
- No job board integrations.
- No voice or video interview implementation.
- No mock LLM output, fake deterministic AI output, fake email provider, or cloud LLM fallback.

## Architecture Overview

- Backend: FastAPI application under `backend/app`, with SQLAlchemy models, Alembic migrations, JWT/RBAC dependencies, SMTP email, and LangGraph workflow modules.
- LLM runtime: LM Studio local OpenAI-compatible API only. The `openai` SDK is used as a local protocol client for LM Studio, not as a cloud fallback.
- Database: PostgreSQL through async SQLAlchemy and Alembic.
- Frontend: Next.js App Router, TypeScript, Tailwind, and React Query under `frontend/`.
- Local services: Docker Compose runs PostgreSQL, Mailpit, backend, and a one-shot migration tool. LM Studio runs separately on the host.
- Evaluation: synthetic fixtures and report-only quality checks under `evals/`, using the same prompts and local LM Studio path as the product code.

## Safety And Hiring Disclaimer

This project is decision-support software for local MVP exploration. It is not a legal compliance engine, an automated hiring decision system, or a substitute for trained human review. Human reviewers own shortlist and final hiring decisions, and deployments must be reviewed for applicable employment, privacy, security, and accessibility requirements before any real candidate use.

## Requirements

- Python 3.11+
- Docker and Docker Compose
- `uv`
- LM Studio running on the host machine with a local model loaded

## Environment

Copy the template:

```bash
cp .env.example .env
```

Required variables:

```bash
DATABASE_URL=postgresql+asyncpg://recruitment:recruitment@localhost:5432/recruitment
# Host backend:
LM_STUDIO_BASE_URL=http://localhost:1234/v1
# Docker backend:
# LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
LM_STUDIO_API_KEY=lm-studio
LM_STUDIO_TEMPERATURE=0.2
LM_STUDIO_TIMEOUT_SECONDS=180
LM_STUDIO_MAX_TOKENS=2048
LM_STUDIO_ENABLE_THINKING=false
SMTP_HOST=localhost
SMTP_PORT=1025
EMAIL_FROM=recruiting@example.local
APP_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:3000
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
JWT_SECRET_KEY=change-me-local-dev-only-32-bytes-minimum
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
DEV_ADMIN_EMAIL=admin@example.local
DEV_ADMIN_PASSWORD=admin-password
DEV_RECRUITER_EMAIL=recruiter@example.local
DEV_RECRUITER_PASSWORD=recruiter-password
DEV_MANAGER_EMAIL=manager@example.local
DEV_MANAGER_PASSWORD=manager-password
```

## Start Infrastructure

Start PostgreSQL and Mailpit:

```bash
docker compose up -d postgres mailpit
```

Mailpit UI is available at [http://localhost:8025](http://localhost:8025).
Interview invite emails use `FRONTEND_BASE_URL` to generate candidate-facing links such as `http://localhost:3000/candidate/interview/{token}`.

## Start LM Studio

1. Open LM Studio on the host machine.
2. Load `qwen/qwen3-4b-2507` for the backend's structured JSON workflows.
3. Start the local server.
4. Set `RECRUITING_LLM_MODEL` in `.env` to the loaded model id shown by LM Studio, and keep `LM_STUDIO_ENABLE_THINKING=false`.
5. Confirm `/health/llm` returns `200` before running AI flows.

LM Studio is not containerized. Use the base URL that matches where FastAPI runs:

```bash
# FastAPI running directly on the host
LM_STUDIO_BASE_URL=http://localhost:1234/v1

# FastAPI running in Docker
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

Inside Docker, `localhost` points to the backend container, not your Mac/Linux/Windows host. The Compose backend service includes `host.docker.internal` support and defaults to that value unless `.env` overrides it.

### Qwen Model Split

Do not use `qwen/qwen3-4b-thinking-2507` as `RECRUITING_LLM_MODEL` for this backend. Its official model card says it supports only thinking mode, and observed LM Studio responses can emit thousands of tokens in `reasoning_content` while leaving `message.content` empty.

Use this split instead:

```bash
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
```

If you intentionally want to test the thinking-only model for JSON workflows, set:

```bash
RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=true
```

That path is expected to be slow and can fail with empty `content` if reasoning consumes the response budget. The backend blocks it by default so a misconfigured workflow fails immediately instead of waiting several minutes per graph node.

The default `qwen/qwen3-4b-2507` model is the hybrid Qwen variant. LM Studio exposes an `Enable Thinking` setting for this model, and the backend also sends `enable_thinking=false` with requests. For the `qwen/qwen3-4b-thinking-2507` variant, those controls do not make it a fast non-thinking model.

## Install And Migrate

```bash
uv sync --dev
uv run alembic upgrade head
```

The backend container intentionally does not run migrations on startup. Run migrations as a separate, visible step so startup does not hide schema failures:

```bash
docker compose --profile tools run --rm migrate
```

To verify a clean database can migrate to head locally:

```bash
scripts/verify_fresh_migration.sh
```

Known technical debt: the initial Alembic revision still delegates table creation to `Base.metadata.create_all()`. Later migrations are explicit, but the initial revision should be converted to explicit `op.create_table` operations before production hardening.

## Run FastAPI

Local process:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Docker backend:

```bash
docker compose up --build backend
```

Swagger docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Run Frontend

The UI Alpha is a Next.js App Router app under `frontend/`.

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000/login](http://localhost:3000/login). The frontend expects the backend at `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.

Use the seeded local users:

- `recruiter@example.local` / `recruiter-password`
- `manager@example.local` / `manager-password`
- `admin@example.local` / `admin-password`

Recruiters can complete the job, calibration, candidate scoring, shortlist, interview-plan, invite, evaluation, final-scorecard, and final-decision flow in the browser. Candidates use the public `/candidate/interview/{token}` route, while the raw token and OTP are retrieved from Mailpit at [http://localhost:8025](http://localhost:8025). Admins can view LLM usage, audit logs, and redacted communication logs at `/admin`.

## Health Checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/llm
```

LM Studio diagnostic:

```bash
uv run python -m app.scripts.check_lmstudio
```

The diagnostic prints the configured base URL and model, checks the OpenAI-compatible `/models` endpoint, runs a tiny real chat completion, and suggests host-vs-Docker fixes. It does not fake health success or use a cloud fallback.

If LM Studio is down, `/health/llm` returns:

```json
{"detail":"LM Studio is not reachable at http://localhost:1234/v1 for model qwen/qwen3-4b-2507. Open LM Studio, start the local server, and load the configured model. If the backend is running in Docker, localhost points to the backend container; set LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1 and recreate the backend container."}
```

`/health/llm` is logged as `health.llm` in `llm_call_logs` with `cache_hit=false`. It is not cached as a business LLM output. If LM Studio returns usage fields, the backend stores `input_tokens` and `output_tokens`; otherwise those fields remain `NULL`.

## Evaluation Quality Evals

Phase 3 evaluation fixtures live under `evals/`. They are synthetic source inputs and expected human review notes, not mock LLM outputs. Run fixture validation without LM Studio:

```bash
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

Run real local-model evals:

```bash
export RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
export LM_STUDIO_BASE_URL=http://localhost:1234/v1
export LM_STUDIO_API_KEY=lm-studio
export LM_STUDIO_TEMPERATURE=0.2
export LM_STUDIO_TIMEOUT_SECONDS=180
export LM_STUDIO_MAX_TOKENS=2048
export LM_STUDIO_ENABLE_THINKING=false
export RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
uv run python -m app.scripts.check_lmstudio
uv run python -m app.scripts.run_evals --all
uv run python -m app.scripts.run_evals --role sales_account_executive
uv run python -m app.scripts.run_evals --stage candidate_scoring
```

Reports are written to `evals/reports/`. If LM Studio is unavailable for an uncached output, the runner fails clearly and does not use fake AI output or a cloud fallback. See `docs/EVALUATION_QUALITY_PLAN.md`.

## Local Upload Storage

Uploaded resumes are written under `backend/data/resumes/{job_id}/` at runtime, and that directory is ignored by git. Intentional test resume fixtures live under `tests/fixtures/resumes/`.

## Local Auth

Recruiter and admin APIs require JWT auth. Candidate interview-entry endpoints remain public and are protected by the emailed interview token plus OTP. After `/start`, active `/answer` and `/complete` calls must also send the returned `client_session_nonce`; the raw nonce is returned once and only its hash is stored.

Public endpoints:

- `/health`, `/health/db`, `/health/llm`
- `/docs`, `/openapi.json`
- `/api/v1/interview-entry/{token}` and its OTP/interview actions

Recruiter/hiring-manager endpoints require `ADMIN`, `RECRUITER`, or `HIRING_MANAGER`.
Admin log endpoints under `/api/v1/admin/*` require `ADMIN`.

Create local development users from environment variables:

```bash
export DEV_ADMIN_EMAIL=admin@example.local
export DEV_ADMIN_PASSWORD=admin-password
export DEV_RECRUITER_EMAIL=recruiter@example.local
export DEV_RECRUITER_PASSWORD=recruiter-password
export DEV_MANAGER_EMAIL=manager@example.local
export DEV_MANAGER_PASSWORD=manager-password

uv run python -m app.scripts.seed_dev_users
```

These env-based users are for local development only. Set a real `JWT_SECRET_KEY` before using the backend outside local development.

Login and pass the bearer token on protected calls:

```bash
RECRUITER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"recruiter@example.local","password":"recruiter-password"}' | jq -r .access_token)

ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.local","password":"admin-password"}' | jq -r .access_token)
```

Communication logs redact raw interview tokens and OTPs before persistence. Mailpit still receives the real link and OTP.

## Full Curl Flow

Set auth headers:

```bash
AUTH_HEADER="Authorization: Bearer $RECRUITER_TOKEN"
ADMIN_AUTH_HEADER="Authorization: Bearer $ADMIN_TOKEN"
```

Create a job:

```bash
JOB_ID=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "department": "Engineering",
    "seniority": "Senior",
    "location": "Remote",
    "employment_type": "Full-time",
    "raw_jd": "We need a senior backend engineer with Python, FastAPI, Postgres, distributed systems, and strong ownership."
  }' | jq -r .id)
```

Run JD calibration through LM Studio:

```bash
curl -X POST http://localhost:8000/api/v1/jobs/$JOB_ID/calibrate \
  -H "$AUTH_HEADER"
```

Optionally edit generated criteria:

```bash
curl -X PATCH http://localhost:8000/api/v1/jobs/$JOB_ID/criteria \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"must_haves_json":["Python","FastAPI","PostgreSQL"]}'
```

Approve criteria as a human:

```bash
curl -X POST http://localhost:8000/api/v1/jobs/$JOB_ID/approve-criteria \
  -H "$AUTH_HEADER"
```

Upload a resume:

```bash
CANDIDATE_ID=$(curl -s -X POST http://localhost:8000/api/v1/jobs/$JOB_ID/candidates/upload-resume \
  -H "$AUTH_HEADER" \
  -F "name=Jane Candidate" \
  -F "email=jane@example.com" \
  -F "file=@tests/fixtures/resumes/jane_backend.txt" | jq -r .id)
```

Process and score the candidate:

```bash
curl -X POST http://localhost:8000/api/v1/candidates/$CANDIDATE_ID/process \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"force": false}'
```

Make a human shortlist decision:

```bash
curl -X POST http://localhost:8000/api/v1/candidates/$CANDIDATE_ID/shortlist-decision \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"decision":"APPROVE","reason":"Meets core backend criteria and should interview."}'
```

Create an interview plan:

```bash
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/candidates/$CANDIDATE_ID/interview-plan \
  -H "$AUTH_HEADER" | jq -r .id)
```

Send the secure invite through Mailpit:

```bash
curl -X POST http://localhost:8000/api/v1/interviews/$SESSION_ID/send-invite \
  -H "$AUTH_HEADER"
```

Open Mailpit, copy the raw interview token link, then:

```bash
TOKEN=<token-from-email-link>
curl http://localhost:8000/api/v1/interview-entry/$TOKEN
curl -X POST http://localhost:8000/api/v1/interview-entry/$TOKEN/send-otp
```

Copy the OTP from Mailpit and verify:

```bash
curl -X POST http://localhost:8000/api/v1/interview-entry/$TOKEN/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"otp":"<otp-from-mailpit>"}'
```

Start the live chat interview and save the client-session nonce:

```bash
START_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/interview-entry/$TOKEN/start)
CLIENT_SESSION_NONCE=$(echo "$START_RESPONSE" | jq -r .client_session_nonce)
echo "$START_RESPONSE" | jq .
```

Answer turn by turn with the nonce:

```bash

curl -X POST http://localhost:8000/api/v1/interview-entry/$TOKEN/answer \
  -H "Content-Type: application/json" \
  -d "{\"answer\":\"I designed FastAPI services backed by PostgreSQL and improved p95 latency by 35%.\",\"client_session_nonce\":\"$CLIENT_SESSION_NONCE\"}"
```

Repeat `/answer` until the response returns `"completed": true`, then complete:

```bash
curl -X POST http://localhost:8000/api/v1/interview-entry/$TOKEN/complete \
  -H "Content-Type: application/json" \
  -d "{\"client_session_nonce\":\"$CLIENT_SESSION_NONCE\"}"
```

Evaluate the interview. This endpoint is idempotent by default: if an evaluation already exists, it returns the latest existing row and does not call LM Studio again. Use `force=true` only for an explicit rerun; forced reruns are recorded in audit metadata.

```bash
curl -X POST http://localhost:8000/api/v1/interviews/$SESSION_ID/evaluate \
  -H "$AUTH_HEADER"

curl -X POST "http://localhost:8000/api/v1/interviews/$SESSION_ID/evaluate?force=true" \
  -H "$AUTH_HEADER"
```

Create the final scorecard. This endpoint has the same idempotency behavior.

```bash
curl -X POST http://localhost:8000/api/v1/candidates/$CANDIDATE_ID/final-scorecard \
  -H "$AUTH_HEADER"

curl -X POST "http://localhost:8000/api/v1/candidates/$CANDIDATE_ID/final-scorecard?force=true" \
  -H "$AUTH_HEADER"
```

Store the final human decision:

```bash
curl -X POST http://localhost:8000/api/v1/candidates/$CANDIDATE_ID/final-decision \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"decision":"HOLD","reason":"Need hiring manager review before final decision."}'
```

Inspect logs:

```bash
curl http://localhost:8000/api/v1/admin/llm-usage -H "$ADMIN_AUTH_HEADER"
curl http://localhost:8000/api/v1/admin/audit -H "$ADMIN_AUTH_HEADER"
curl http://localhost:8000/api/v1/admin/communications -H "$ADMIN_AUTH_HEADER"
```

## Tests And Lint

Use the validation cadence in [Development Workflow](docs/DEVELOPMENT_WORKFLOW.md). Do not run full verification after every small task.

Small backend-only task:

```bash
uv run python scripts/check_backend_fast.py
```

Small frontend-only task:

```bash
cd frontend
npm run check:fast
```

Batch of 3-4 tasks or pre-commit checkpoint:

```bash
uv run python scripts/check_checkpoint.py
```

End of phase or major merge:

```bash
uv run python scripts/check_full.py
```

Only after AI prompt/schema/scoring/eval-helper changes:

```bash
uv run python scripts/check_eval_targeted.py --stage candidate_scoring
```

Only before declaring an AI quality milestone:

```bash
uv run python scripts/check_eval.py
```

Individual checks remain available:

```bash
uv run pytest -q
uv run pytest -q -m unit
RUN_DB_TESTS=true uv run pytest -q -m db
RUN_MAILPIT_TESTS=true uv run pytest -q -m mailpit
RUN_LMSTUDIO_TESTS=true uv run pytest -q -m lmstudio
RUN_E2E=true uv run pytest -q -m e2e
RUN_SLOW_TESTS=true uv run pytest -q -m slow
uv run ruff check backend/app tests

cd frontend
npm run check:fast
npm run typecheck
npm run lint
npm run test
npm run build
```

Pytest markers separate `unit`, `db`, `mailpit`, `lmstudio`, `e2e`, and `slow` tests, and unknown markers fail collection. Unit tests must not require external services. External and slow tests are skipped unless their explicit `RUN_*` flag is set. LM Studio integration tests must make real local model calls and should fail clearly when enabled but unavailable.

## Known Limitations

- The MVP is local-first and has not been hardened for production hosting.
- The initial Alembic revision still delegates table creation to `Base.metadata.create_all()`.
- The eval framework uses synthetic fixtures and report-only heuristics; it is not a legal or statistical validation suite.
- Candidate interview recovery depends on browser session storage during an active chat.
- Playwright E2E is not configured yet.
- Voice/video interviews, coding assessments, ATS sync, LinkedIn scraping, and job-board integrations are intentionally out of scope.

## Roadmap

- Convert the initial migration to explicit Alembic operations.
- Add CI-backed PostgreSQL migration tests and broader integration coverage.
- Add rate limiting and retention policies for interview-entry, communication, LLM, upload, and eval data.
- Add explicit pilot runbooks for backup/restore, secret rotation, migration rollback, and incident handling.
- Tune eval score-band calibration and broaden synthetic fixture coverage.
- Add full browser E2E only when the local stack can run reliably in CI or a dedicated developer script.

## Project Docs

- [Frontend README](frontend/README.md)
- [Development workflow](docs/DEVELOPMENT_WORKFLOW.md)
- [LM Studio settings](docs/LM_STUDIO_SETTINGS.md)
- [Evaluation quality plan](docs/EVALUATION_QUALITY_PLAN.md)
- [Eval triage report](docs/EVAL_TRIAGE_REPORT.md)
- [Next steps](docs/NEXT_STEPS.md)
- [Open-source readiness](docs/OPEN_SOURCE_READINESS.md)
- [License decision](docs/LICENSE_DECISION.md)

## License Status

No open-source license has been selected yet. The maintainer must add a `LICENSE` file before publishing if they want others to use, modify, or redistribute the code.
