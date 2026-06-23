# Recruitment Agent Frontend

Next.js App Router frontend for the FastAPI + LangGraph recruiting MVP.

## Install

```bash
cd frontend
npm install
cp .env.example .env.local
```

Set:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The browser client calls this backend URL directly. The backend `.env` should include `CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` for local development.

## Run

Start the backend services first from the repo root:

```bash
docker compose up -d postgres mailpit
uv run alembic upgrade head
uv run uvicorn app.main:app --app-dir backend --reload
```

Seed local users if needed:

```bash
uv run python -m app.scripts.seed_dev_users
```

Then run the frontend:

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Required local services:

- FastAPI backend: [http://localhost:8000](http://localhost:8000)
- Mailpit UI: [http://localhost:8025](http://localhost:8025)
- LM Studio local server: [http://localhost:1234/v1](http://localhost:1234/v1)

LM Studio must be open, the local server must be started, and the configured non-thinking model must be loaded before AI flows. Confirm backend health first:

```bash
curl http://localhost:8000/health/llm
```

Use `LM_STUDIO_BASE_URL=http://localhost:1234/v1` when the backend runs directly on the host. Use `LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1` when the backend runs in Docker.

## Login Flow

Use the dev credentials configured in the backend `.env`, for example:

- `recruiter@example.local` / `recruiter-password`
- `manager@example.local` / `manager-password`
- `admin@example.local` / `admin-password`

The login page calls `POST /api/v1/auth/login`, stores the JWT in local storage for the local MVP, and sends `Authorization: Bearer <token>` on protected requests. Recruiter/admin pages call `GET /api/v1/auth/me` and redirect to `/login` on `401`.

## Candidate Interview Flow

The candidate route is public:

```text
/candidate/interview/{token}
```

It calls the backend interview-entry endpoints without a JWT, sends OTP through Mailpit/local SMTP, verifies OTP, starts the interview, stores the returned `client_session_nonce` in session storage, and includes that nonce in answer/complete calls.

Mailpit is available at [http://localhost:8025](http://localhost:8025). The backend invite email should contain a frontend link like `http://localhost:3000/candidate/interview/{token}`. If an older email contains `/api/v1/interview-entry/{token}`, use the same token in `/candidate/interview/{token}`.

## Recruiter MVP Browser Flow

1. Login at [http://localhost:3000/login](http://localhost:3000/login).
2. Create a job from `/jobs/new`.
3. Run JD calibration and wait for LM Studio.
4. Review/edit criteria on `/jobs/{jobId}` and approve criteria.
5. Upload a resume from the job detail or candidate list page.
6. Process the candidate and review the persisted latest score/evidence on `/candidates/{candidateId}`.
7. Submit a shortlist decision with a reason.
8. Generate an interview plan, review it from the candidate interview-session list, and send the invite.
9. Retrieve the candidate link and OTP from Mailpit.
10. After the candidate completes the interview, open `/interviews/{sessionId}/evaluation`, evaluate the transcript, and generate `/candidates/{candidateId}/final`.
11. Submit the final human decision with a reason.
12. Login as admin and open `/admin` to review LLM, audit, and redacted communication logs.

## Candidate Browser Flow

1. Open Mailpit at [http://localhost:8025](http://localhost:8025).
2. Open the latest `Your interview invitation` email.
3. Open the frontend invite link: `/candidate/interview/{token}`.
4. Send OTP from the candidate page.
5. Copy the OTP from Mailpit and verify it.
6. Start the interview and keep the tab open.
7. Answer each question until the UI shows completion.

The candidate page stores `client_session_nonce` and the current turn in `sessionStorage`. A refresh during an active interview can continue only if that browser state is still present; otherwise the UI shows a recovery message and the candidate should return to the original tab or contact the recruiter.

## Checks

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

## Known Limitations

- The UI does not mock AI outputs or simulate success. Long-running calibration, processing, evaluation, and final scorecard actions depend on the real backend and LM Studio state.
- Playwright E2E is not configured yet. Full browser E2E should be added only when the local stack can run reliably in CI or an explicit `RUN_E2E=true` workflow.

## QA Docs

- [UI QA report](docs/UI_QA_REPORT.md)
- [Dependency audit](docs/DEPENDENCY_AUDIT.md)
