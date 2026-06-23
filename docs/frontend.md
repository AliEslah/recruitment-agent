# Frontend

The frontend is a Next.js App Router application under `frontend/`. It supports local recruiter, manager, admin, and public candidate interview flows against the FastAPI backend.

## Run Locally

Start backend services first:

```bash
docker compose up -d postgres mailpit
uv run alembic upgrade head
uv run uvicorn app.main:app --app-dir backend --reload
```

Then start the frontend:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Set:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Open [http://localhost:3000/login](http://localhost:3000/login).

## Main Routes

- `/login`
- `/jobs`
- `/jobs/new`
- `/jobs/{jobId}`
- `/candidates/{candidateId}`
- `/interviews`
- `/interviews/{sessionId}/evaluation`
- `/candidates/{candidateId}/final`
- `/candidate/interview/{token}`
- `/admin`

## Candidate Flow

The candidate route is public. It sends OTP through the backend, verifies OTP, starts the interview, stores the returned `client_session_nonce` in session storage, and includes that nonce in active answer and complete calls.

Mailpit is available at [http://localhost:8025](http://localhost:8025) for local invite and OTP emails. Do not paste real candidate links, OTPs, or raw tokens into public issues or docs.

## Checks

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

The UI does not mock AI output. Long-running AI actions depend on the backend and LM Studio state.
