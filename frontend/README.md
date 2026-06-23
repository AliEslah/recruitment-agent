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
3. Optionally select a pilot role template to prefill editable job fields.
4. Run JD calibration and approve criteria.
5. Upload a synthetic or local test resume.
6. Process the candidate and submit a shortlist decision.
7. Generate an interview plan and send the invite.
8. Retrieve the candidate link and OTP from Mailpit.
9. Complete the public candidate interview at `/candidate/interview/{token}` and submit candidate feedback.
10. Evaluate the interview, generate a final scorecard, print or save it through browser print, submit scorecard feedback, and submit a human final decision.
11. Log in as admin and review logs, feedback, and pilot summary.

The candidate page stores the active `client_session_nonce` in session storage and sends it with answer and complete calls.

## Pilot UI

- `/jobs/new` can prefill editable fields from backend role templates.
- Final scorecards include the advisory disclaimer and a `Print / Save as PDF` browser-print action.
- Recruiters and hiring managers can submit scorecard feedback from the final scorecard page.
- Candidates can submit interview feedback after completion.
- Admin users can review feedback and pilot counts in `/admin`.

The frontend never simulates successful AI output. Long-running AI actions still call the backend, which calls LM Studio.

Phase 4B pilot verification does not run full LLM evals. Use backend fixture validation only:

```bash
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

Frontend readiness commands:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

If Docker is unavailable, PostgreSQL, Mailpit, and the backend container cannot be verified. Start Docker and rerun `../scripts/verify_pilot_readiness.sh`.

If LM Studio is unreachable, start LM Studio, load the configured model, set `RECRUITING_LLM_MODEL`, `LM_STUDIO_BASE_URL`, and `LM_STUDIO_API_KEY`, then rerun `uv run python -m app.scripts.check_lmstudio` from the repository root.

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
