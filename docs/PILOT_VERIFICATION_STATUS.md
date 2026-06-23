# Pilot Verification Status

- Date/time: 2026-06-23 16:46:13 Asia/Tehran (`+0330`).
- Environment: local Codex workspace at `/Users/eslah/Project/recruitment-agent`.
- Phase: Phase 4B operational verification.
- Policy: full LLM evals were not run. Only `uv run python -m app.scripts.run_evals --dry-run-fixtures` was used.
- LLM: LM Studio local OpenAI-compatible API with `qwen/qwen3-4b-2507`.

## Current Status

| Area | Status | Evidence |
| --- | --- | --- |
| Docker | PASS | `docker compose ps` reported `backend`, `postgres`, and `mailpit` running. |
| PostgreSQL | PASS | `recruitment-agent-postgres-1` running and healthy on port `5432`. |
| Mailpit | PASS | `recruitment-agent-mailpit-1` running and healthy on ports `1025` and `8025`. |
| Backend container | PASS | `recruitment-agent-backend-1` running on port `8000`. |
| Backend health | PASS | `/health`, `/health/db`, and `/health/llm` returned `ok`. |
| LM Studio | PASS | `uv run python -m app.scripts.check_lmstudio` reached `/models`, verified `qwen/qwen3-4b-2507`, and completed one tiny chat diagnostic. |
| Migrations | PASS | `uv run alembic upgrade head` completed through head after making the existing `0006` metadata column migration idempotent for fresh databases. |
| Seed status | PASS | `uv run python -m app.scripts.seed_dev_users` and `uv run python -m app.scripts.seed_pilot_data` completed. Pilot seed data contains human-authored fixtures only. |
| Role templates | PASS | Role templates were loaded by the pilot seed and used to create a Backend Engineer job in the browser flow. |
| Backend tests | PASS | `uv run pytest -q` passed: 102 tests. |
| Backend Ruff | PASS | `uv run ruff check backend/app tests` passed. |
| Frontend checks | PASS | `npm run typecheck`, `npm run lint`, `npm run test`, and `npm run build` passed. |
| Eval dry-run fixtures | PASS | `uv run python -m app.scripts.run_evals --dry-run-fixtures` loaded 7 fixture sets. No full or stage-specific LLM evals were run. |
| Readiness script | PASS | `scripts/verify_pilot_readiness.sh` completed with exit code `0` using real local services. |
| Manual pilot flow | PASS | Browser flow completed end to end with real local backend, PostgreSQL, Mailpit, frontend dev server, and LM Studio. |

## Manual Flow Evidence

| Step | Status | Evidence |
| --- | --- | --- |
| Recruiter login | PASS | Logged in as `pilot.recruiter@example.local`. |
| Create job from role template | PASS | Created Backend Engineer job from a role template and edited the raw JD. |
| Calibration and criteria approval | PASS | Ran JD calibration, reviewed generated criteria, and approved criteria. |
| Candidate upload and scoring | PASS | Uploaded the backend engineer pilot resume using `pilot.backend.candidate@example.com`, processed candidate, and verified score `85%` with evidence. |
| Shortlist approval | PASS | Approved shortlist with a required human reason. |
| Interview plan and invite | PASS | Generated a five-question plan with fixed, resume-validation, soft-skill, knockout, and dynamic question types; sent invite through Mailpit. |
| Candidate OTP flow | PASS | Candidate opened the Mailpit invite link, requested OTP, retrieved OTP from Mailpit, verified OTP, and started the interview. |
| Candidate interview | PASS | Candidate answered all five questions and reached completed state. |
| Candidate feedback | PASS | Candidate submitted interview feedback; admin feedback tab later showed the record. |
| Interview evaluation | PASS | Recruiter viewed transcript, generated interview evaluation, and verified score `88%`, recommendation, confidence, evidence, and missing-evidence sections. |
| Final scorecard | PASS | Generated final scorecard with advisory human-review disclaimer, resume/interview/overall scores, evidence summary, missing evidence, and confidence. |
| Print/save scorecard | PASS | Saved the final scorecard to `output/playwright/pilot-final-scorecard.pdf` using Playwright PDF capture. |
| Final decision | PASS | Submitted final human decision `HOLD` with a required reason; candidate status updated to `FINAL_REVIEW`. |
| Scorecard feedback | PASS | Recruiter submitted scorecard feedback; admin feedback tab showed the record. |
| Admin feedback view | PASS | Admin saw both recruiter scorecard feedback and candidate interview feedback. |
| Admin LLM usage logs | PASS | Admin LLM tab showed successful local LM Studio calls for health, JD calibration, resume parsing/scoring, interview planning/evaluation, and final scorecard generation. |
| Admin audit logs | PASS | Admin audit tab showed criteria approval, shortlist decision, invite, interview evaluation, final scorecard generation, and final decision records. |
| Admin communication logs | PASS | Admin communication tab showed invite and OTP emails with `[REDACTED_INTERVIEW_TOKEN]` and `[REDACTED_OTP]`. |

## Notes

- The first attempted candidate email used a `.local` address and was rejected by frontend/backend validation. Retrying with `pilot.backend.candidate@example.com` passed.
- The pilot summary pane reports no recent LLM failures. The dedicated LLM usage tab contains the successful LLM call history.
- Browser console contained non-blocking entries from the missing favicon, the intentional invalid-email upload attempt, and a repeated evaluation request after evaluation already existed.
- No mock LLM output, fake AI output, cloud LLM provider, or cloud fallback was introduced.

## Blockers

None for the verified local pilot run.

## Next Actions

1. Keep Docker, PostgreSQL, Mailpit, backend, frontend, and LM Studio running during pilot sessions.
2. Use `scripts/verify_pilot_readiness.sh` before each controlled pilot session.
3. Keep using only `run_evals --dry-run-fixtures` during Phase 4B unless prompts, schemas, evidence grounding, protected-term scanning, recommendation bands, or expected fixture behavior change.
4. For a production pilot, decide on the follow-up items in `docs/NEXT_STEPS.md` before expanding beyond controlled local use.
