# Backend

The backend is a FastAPI application under `backend/app`. It exposes authenticated recruiter, manager, and admin APIs plus public candidate interview-entry APIs protected by invite token, OTP, and client-session nonce checks.

## Run Locally

```bash
docker compose up -d postgres mailpit
uv sync --dev
uv run alembic upgrade head
uv run python -m app.scripts.seed_dev_users
uv run uvicorn app.main:app --app-dir backend --reload
```

Swagger docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Key APIs

- `GET /health`
- `GET /health/db`
- `GET /health/llm`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/jobs`
- `POST /api/v1/jobs/{job_id}/calibrate`
- `POST /api/v1/jobs/{job_id}/approve-criteria`
- `POST /api/v1/jobs/{job_id}/candidates/upload-resume`
- `POST /api/v1/candidates/{candidate_id}/process`
- `POST /api/v1/candidates/{candidate_id}/shortlist-decision`
- `POST /api/v1/candidates/{candidate_id}/interview-plan`
- `POST /api/v1/interviews/{session_id}/send-invite`
- `POST /api/v1/interviews/{session_id}/evaluate`
- `POST /api/v1/candidates/{candidate_id}/final-scorecard`
- `POST /api/v1/candidates/{candidate_id}/final-decision`
- `GET /api/v1/admin/llm-usage`
- `GET /api/v1/admin/audit`
- `GET /api/v1/admin/communications`

Candidate entry APIs are public but require the invite token path and OTP flow:

- `GET /api/v1/interview-entry/{token}`
- `POST /api/v1/interview-entry/{token}/send-otp`
- `POST /api/v1/interview-entry/{token}/verify-otp`
- `POST /api/v1/interview-entry/{token}/start`
- `POST /api/v1/interview-entry/{token}/answer`
- `POST /api/v1/interview-entry/{token}/complete`

## Auth

Recruiter, manager, and admin APIs use JWT bearer auth. Candidate interview-entry endpoints intentionally do not require recruiter JWT auth, because candidates access them from emailed links. Raw interview tokens and OTPs are delivery secrets and must not be logged or committed.

Seed local users with:

```bash
uv run python -m app.scripts.seed_dev_users
```

## Migrations

Run migrations explicitly:

```bash
uv run alembic upgrade head
```

The backend container does not hide schema failures by running migrations on startup. For Docker:

```bash
docker compose --profile tools run --rm migrate
```

Known technical debt: the initial Alembic revision still delegates table creation to SQLAlchemy metadata. Later migrations are explicit.

## Validation

```bash
uv run pytest -q
uv run ruff check backend/app tests
uv run alembic upgrade head
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

External-service tests are gated by explicit `RUN_*` environment flags. Unit tests must not require LM Studio, Mailpit, Docker services, or real eval runs.
