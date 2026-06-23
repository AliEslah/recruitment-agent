# Pilot Runbook

## Pilot Goal

Run a controlled pilot with real recruiting teams to validate whether the platform helps recruiters create a job from a raw JD, calibrate criteria, upload resumes, score candidates, approve a shortlist, send a secure live chat interview, evaluate the interview, and produce an evidence-based final scorecard.

AI recommendations are advisory. A qualified human reviewer owns shortlist and final hiring decisions.

Phase 4B is operational verification, not evaluation-quality testing. Full LLM evals and stage-specific LLM evals are not run in this phase. Use only `uv run python -m app.scripts.run_evals --dry-run-fixtures` unless prompt text, schemas, grounding, protected-term scanning, recommendation bands, or expected eval behavior changed.

## Target Pilot Users

- Recruiters who own job setup, resume upload, shortlist review, and interview invites.
- Hiring managers who review criteria, scorecards, and final recommendations.
- Admins who monitor logs, feedback, and local service health.
- Candidates who complete secure chat interviews after receiving consent language and an invite.

## Recommended Pilot Size

- 2-5 recruiting teams.
- 3-5 job positions.
- 20-50 candidates.
- 5-10 live chat interviews.

## Required Local Services

- PostgreSQL.
- Mailpit or SMTP.
- FastAPI backend.
- Next.js frontend.
- LM Studio local server.
- Loaded non-thinking structured-output model.

## Setup Checklist

1. Copy `.env.example` to `.env` and set local secrets.
2. Start PostgreSQL and Mailpit: `docker compose up -d postgres mailpit`.
3. Install backend dependencies: `uv sync --dev`.
4. Apply migrations: `uv run alembic upgrade head`.
5. Start LM Studio, enable the local server, and load `RECRUITING_LLM_MODEL`.
6. Export LM Studio environment:

   ```bash
   export RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
   export LM_STUDIO_BASE_URL=http://localhost:1234/v1
   export LM_STUDIO_API_KEY=lm-studio
   ```

7. Check LM Studio with the tiny diagnostic only: `uv run python -m app.scripts.check_lmstudio`.
8. Run eval fixture dry run only: `uv run python -m app.scripts.run_evals --dry-run-fixtures`.
9. Seed local users: `uv run python -m app.scripts.seed_dev_users`.
10. Seed pilot starter content: `uv run python -m app.scripts.seed_pilot_data`.
11. Start backend: `docker compose up -d --build backend` or `uv run uvicorn app.main:app --app-dir backend --reload`.
12. Start frontend from `frontend/`: `npm install` then `npm run dev`.
13. Run `scripts/verify_pilot_readiness.sh`.
14. Complete `docs/PILOT_MANUAL_VERIFICATION.md`.

## User Creation Checklist

- Confirm admin, recruiter, and hiring manager accounts exist.
- Use unique accounts per pilot participant where practical.
- Confirm each user can log in.
- Confirm only admin users can open admin logs and pilot summary.
- Rotate local pilot passwords before inviting external pilot teams.

## LM Studio Checklist

- Local server is running at `LM_STUDIO_BASE_URL`.
- `RECRUITING_LLM_MODEL` exactly matches the loaded model id.
- Thinking mode is disabled for JSON workflows.
- `LM_STUDIO_ENABLE_THINKING=false`.
- `RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false`.
- `/health/llm` and `check_lmstudio` pass before the demo.
- If the backend runs inside Docker and cannot reach host LM Studio, set `LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1`.

## Demo Reset Checklist

- Confirm no real candidate data is mixed with demo data.
- Re-run migrations if the database was recreated.
- Run `uv run python -m app.scripts.seed_pilot_data`.
- Delete runtime uploads under `backend/data/resumes/` only when you intentionally reset local demo inputs.
- Do not seed fake scores, fake interview evaluations, fake final scorecards, or fake LLM output.

## Main Pilot Flow

1. Recruiter logs in.
2. Recruiter creates a job from a raw JD or selects a role template to prefill editable fields.
3. Recruiter runs calibration through LM Studio.
4. Recruiter reviews and edits criteria.
5. Human reviewer approves criteria.
6. Recruiter uploads candidate resumes.
7. Recruiter processes candidates through LM Studio.
8. Recruiter or hiring manager approves shortlist decisions.
9. Recruiter generates an interview plan.
10. Recruiter sends the secure live chat invite.
11. Candidate verifies OTP and completes the chat interview.
12. Recruiter evaluates the interview through LM Studio.
13. Recruiter generates the final scorecard through LM Studio.
14. Human reviewer records the final decision.
15. Pilot user prints or saves the final scorecard as PDF through browser print.
16. Pilot user submits feedback.
17. Admin reviews feedback, audit logs, communication logs, LLM failures, and pilot summary.

## Failure Recovery

- LM Studio unavailable: keep the failed screen visible, start or reload the model, run `check_lmstudio`, then retry the same action.
- Docker unavailable: start Docker Desktop or the Docker daemon, then run `docker compose up -d postgres mailpit`; do not mark verification passed until containers are verified.
- JSON generation fails: review `backend/data/llm_failures/`, confirm model settings, and retry with `force` only when the user intentionally wants a rerun.
- SMTP/Mailpit unavailable: restart Mailpit or fix SMTP settings, then resend invite or OTP.
- Candidate loses browser session after starting: create a new interview invite; the nonce is intentionally single-session.
- Database error: stop writes, back up current data if needed, inspect migrations, and rerun `uv run alembic upgrade head`.

## Data Privacy Notes

- Use the smallest candidate data set required for the pilot.
- Do not upload production candidate data into demo resets.
- Keep runtime resumes and LLM failure payloads out of git.
- Review audit, communication, and feedback logs before sharing screenshots.
- Export logs only to approved internal storage.

## Candidate Consent Notes

- Tell candidates the interview is a text chat with AI assistance.
- Explain that AI output is advisory and a human makes the decision.
- Explain what data is collected: resume, chat transcript, OTP/security events, and feedback if submitted.
- Provide a non-AI alternative if required by the pilot sponsor or local policy.

## Do Not Use Yet

- No high-stakes automated hiring decisions.
- No voice or video interviews.
- No coding assessments.
- No LinkedIn scraping.
- No job board integrations.
- No full ATS replacement workflows.
- No protected attributes for scoring or questions.
- No compliance-certified decision reports.

## Success Metrics

- Time to shortlist.
- Recruiter agreement with AI shortlist.
- Hiring manager trust in scorecard.
- Candidate interview completion rate.
- Number of manual corrections.
- Number of unsupported evidence reports.
- Number of rejected AI recommendations.
- User-reported usefulness.

## Feedback Collection Plan

- Recruiters submit scorecard feedback on the final scorecard page.
- Hiring managers submit scorecard feedback on the same page while logged in.
- Candidates submit interview feedback after completing the public interview flow.
- Admin reviews `/admin` feedback and pilot summary daily during the pilot.
- Track rating, comment themes, manual corrections, rejected recommendations, and unsupported evidence reports after each pilot job.

## Demo Data Policy

Allowed seed content:

- Pilot users.
- Role templates.
- Question-bank starter items.
- Synthetic raw JD examples.
- Synthetic resume files and candidate input records.

Not allowed:

- Pre-seeded fake AI scores.
- Fake interview evaluations.
- Fake final scorecards.
- Fake LLM outputs pretending to be real.
- Cloud LLM fallback.
