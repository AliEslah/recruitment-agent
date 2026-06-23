# Phase 1B Reliability And Cleanup

Date: 2026-06-22

Status: complete for the scoped backend reliability pass.

## Completed

- Added explicit local migration paths:
  - `uv run alembic upgrade head`
  - `docker compose --profile tools run --rm migrate`
  - `scripts/verify_fresh_migration.sh`
- Added Alembic revisions `20260622_0004_reliability_indexes_nonce.py` and `20260622_0005_chat_only_interview_mode.py`.
- Added the requested SQLAlchemy model indexes and matching migration indexes for candidates, scores, interview sessions/messages/evaluations, final scorecards, human decisions, audit logs, communication logs, and LLM call logs.
- Added `interview_sessions.client_session_hash`.
- Changed `/api/v1/interview-entry/{token}/start` to return `client_session_nonce` once and store only its hash.
- Required `client_session_nonce` on `/answer` and `/complete` while an interview is active.
- Logged `MULTIPLE_SESSION_ATTEMPT` for second-client starts and invalid/missing active-session nonce attempts.
- Made `POST /api/v1/interviews/{session_id}/evaluate` idempotent by default.
- Made `POST /api/v1/candidates/{candidate_id}/final-scorecard` idempotent by default.
- Added `force=true` reruns for evaluation and final scorecard generation, with audit metadata marking forced reruns.
- Added `backend/app/services/status_transitions.py` and wired it into the main job, candidate, and interview mutation paths.
- Added LM Studio response usage parsing. `input_tokens` and `output_tokens` are stored when LM Studio returns them and left `NULL` otherwise.
- Logged `/health/llm` as task `health.llm` with `cache_hit=false`, without writing health responses to the business LLM cache.
- Deleted unused `src/recruitment_agent` code instead of retaining an archive.
- Removed the old `LM_STUDIO_MODEL` fallback, unused reasoning-model setting, and unimplemented `VOICE`/`VIDEO` interview modes.
- Removed `COPY src` from the Docker image path.
- Moved the resume fixture to `tests/fixtures/resumes/jane_backend.txt`.
- Ignored runtime upload and raw LLM failure directories in `.gitignore`.
- Added conservative ORM relationships without delete cascades.
- Kept candidate score recommendations enum-like and interview/final scorecard recommendations narrative, with `Text` DB columns and 2000-character schema limits.
- Added pytest markers: `unit`, `db`, `mailpit`, `lmstudio`, and `e2e`.

## Verification

- `uv run ruff check backend/app tests`
- `uv run pytest -q`

## Remaining Technical Debt

- The initial migration still uses `Base.metadata.create_all()`. This was documented and left unchanged because the task explicitly said not to rewrite the initial migration unless necessary.
- The migration verification script currently expects local Docker Compose PostgreSQL. It should be run in CI once CI has a PostgreSQL service.
- Existing integration coverage is still mostly unit-level. DB, Mailpit, LM Studio, and full-flow tests are marked and documented but should be expanded in CI/pilot hardening.
- Candidate processing and interview planning could gain optional idempotency based on `resume_hash` or existing draft sessions, but that was optional and not implemented in this pass.
