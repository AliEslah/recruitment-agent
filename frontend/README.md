# Recruitment Agent Frontend

Next.js App Router frontend for the local-first AI Recruiting Decision Platform.

## Setup

Start backend services from the repository root:

```bash
docker compose up -d postgres mailpit
uv run alembic upgrade head
uv run uvicorn app.main:app --app-dir backend --reload
```

Then run the frontend:

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

## Local Services

- FastAPI backend: [http://localhost:8000](http://localhost:8000)
- Mailpit UI: [http://localhost:8025](http://localhost:8025)
- LM Studio local API: [http://localhost:1234/v1](http://localhost:1234/v1)

LM Studio must be running with the configured local model before AI flows will complete. The UI does not simulate successful AI output.

## Browser Flow

1. Log in as a seeded recruiter.
2. Create a job.
3. Run JD calibration and approve criteria.
4. Upload a synthetic or local test resume.
5. Process the candidate and submit a shortlist decision.
6. Generate an interview plan and send the invite.
7. Retrieve the candidate link and OTP from Mailpit.
8. Complete the public candidate interview at `/candidate/interview/{token}`.
9. Evaluate the interview, generate a final scorecard, and submit a human final decision.
10. Log in as admin and review logs.

The candidate page stores the active `client_session_nonce` in session storage and sends it with answer and complete calls.

## Checks

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

Fast local check:

```bash
npm run check:fast
```

See [../docs/frontend.md](../docs/frontend.md), [../docs/getting-started.md](../docs/getting-started.md), and [docs/DEPENDENCY_AUDIT.md](docs/DEPENDENCY_AUDIT.md).
