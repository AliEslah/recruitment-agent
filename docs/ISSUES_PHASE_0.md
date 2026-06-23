# Phase 0 Issues

Historical issue counts after the Phase 0 audit, before the Phase 1B reliability pass:

- P0: 0 open
- P1: 8 open
- P2: 5 open
- Fixed during audit/security pass: 3

Phase 1B resolved the scoped P1/P2 reliability and cleanup items except for the intentionally deferred initial-migration rewrite and broader integration-test expansion. See `docs/ISSUES_PHASE_1B.md` for current status.

## P0 Blockers

### P0-1: Raw interview token and OTP are stored in communication logs

Status: fixed in the P0 security pass.

Description: `EmailService` persists the full email body in `communication_logs.body`. Invite emails include the raw interview token link, and OTP emails include the raw OTP. `InterviewSession` stores hashes correctly, but the secrets remain recoverable from communication logs.

Affected files:

- `backend/app/services/email.py`
- `backend/app/api/v1/interviews.py`
- `backend/app/db/models.py`

Acceptance criteria:

- Communication logs do not store raw interview tokens or raw OTPs.
- Logs still contain enough metadata to audit template, recipient, status, and delivery errors.
- Existing candidate email delivery still works through Mailpit.
- Tests prove the persisted communication body or metadata is redacted.

### P0-2: No authentication or authorization protects recruiter/admin APIs

Status: fixed in the P0 security pass.

Description: All API routes are publicly callable in the local backend, including `/api/v1/admin/audit`, `/api/v1/admin/llm-usage`, `/api/v1/admin/communications`, candidate data, job data, decisions, and scorecards. `User` exists, but there is no auth dependency or RBAC enforcement.

Affected files:

- `backend/app/api/v1/*.py`
- `backend/app/db/models.py`
- `backend/app/schemas/common.py`

Acceptance criteria:

- Admin and recruiter endpoints require authenticated users.
- Candidate interview entry endpoints remain token/OTP based and do not require recruiter auth.
- Admin routes require admin role.
- Human decisions are tied to an authenticated user or explicitly documented local-only mode.
- Tests cover unauthorized and authorized access.

## P1 Important Fixes

### P1-1: Migrations are not run by Docker backend startup

Description: The backend container starts Uvicorn directly. A fresh database requires a separate `uv run alembic upgrade head` step.

Affected files:

- `Dockerfile`
- `docker-compose.yml`
- `README.md`

Acceptance criteria:

- Local setup clearly runs migrations before backend use, either as a documented command or a separate migration service.
- Backend startup does not hide migration failures.
- Fresh database bootstrap is tested.

### P1-2: Initial migration uses `Base.metadata.create_all()`

Description: The initial Alembic migration delegates schema creation to current model metadata. That makes historical migrations depend on current model code and weakens repeatability.

Affected files:

- `alembic/versions/20260622_0001_initial_recruiting_platform.py`

Acceptance criteria:

- Initial migration contains explicit `op.create_table`, enum, index, and constraint operations.
- Rebuilding from an empty database creates the same schema as the model snapshot intended for that revision.
- Migration downgrade does not drop unrelated objects accidentally.

### P1-3: Missing indexes for common query paths

Description: The schema mostly relies on primary keys and unique constraints. Repeated queries sort/filter by job, candidate, session, and created time without supporting indexes.

Affected files:

- `backend/app/db/models.py`
- `alembic/versions/*`
- repositories under `backend/app/repositories`

Acceptance criteria:

- Add indexes for candidates by `job_id`, scores by `(candidate_id, job_id, created_at)`, interview messages by `(interview_session_id, created_at)`, evaluations by `(interview_session_id, created_at)`, final scorecards by `(candidate_id, job_id, created_at)`, logs by `created_at`, and LLM logs by relevant filter columns.
- Query plans for repository methods use indexes on realistic row counts.

### P1-4: `/health/llm` bypasses LLM call logging

Description: Workflow calls use `LLMJsonService` and create `LlmCallLog`, but `/health/llm` calls `LMStudioClient` directly and leaves no audit trail.

Affected files:

- `backend/app/api/v1/health.py`
- `backend/app/services/lmstudio.py`
- `backend/app/services/llm_json.py`

Acceptance criteria:

- Health LLM calls are either intentionally excluded and documented, or logged with task `health.llm`.
- Logging does not cache health responses as business outputs.
- Failure status is visible in logs.

### P1-5: LLM token usage fields are not populated

Description: `LlmCallLog` has `input_tokens`, `output_tokens`, and `estimated_cost`, but the service never extracts usage from OpenAI-compatible responses.

Affected files:

- `backend/app/services/lmstudio.py`
- `backend/app/services/llm_json.py`
- `backend/app/db/models.py`

Acceptance criteria:

- Available LM Studio usage fields are captured when present.
- Missing usage is represented as `NULL`, not fabricated.
- Tests cover both usage-present and usage-missing responses.

### P1-6: `single_session_lock` does not actually bind answer requests to one client session

Description: `/start` sets `single_session_lock`, but `/answer` only checks the token. Any client with the token can continue answering during an active interview.

Affected files:

- `backend/app/api/v1/interviews.py`
- `backend/app/agents/interview/live_graph.py`
- `backend/app/db/models.py`

Acceptance criteria:

- Starting an interview returns or sets a session-bound nonce.
- `/answer` requires that nonce while the interview is active.
- Duplicate active clients are rejected and security events are logged.
- Tests cover second-client attempts.

### P1-7: Repeated evaluation and scorecard calls create duplicate rows

Description: Re-running evaluation and final scorecard endpoints inserts new records instead of returning the latest existing result or requiring `force=true`.

Affected files:

- `backend/app/api/v1/interviews.py`
- `backend/app/api/v1/decisions.py`
- `backend/app/agents/interview/evaluation_graph.py`
- `backend/app/agents/final_decision/graph.py`

Acceptance criteria:

- Repeated calls are idempotent by default or require an explicit force flag.
- Audit/LLM logs make reruns clear.
- Tests cover repeated calls.

### P1-8: Status transitions are spread across endpoints and graph nodes

Description: Job, candidate, and interview status changes are implemented inline in multiple endpoints and nodes. Some transitions are guarded, while others are permissive, for example approving criteria without checking generated criteria.

Affected files:

- `backend/app/api/v1/jobs.py`
- `backend/app/api/v1/candidates.py`
- `backend/app/api/v1/interviews.py`
- graph node files under `backend/app/agents`

Acceptance criteria:

- Central transition helpers define allowed current and next statuses.
- Invalid transitions return clear 409/422 errors.
- Tests cover the main MVP happy path and invalid orderings.

## P2 Cleanup

### P2-1: Remove unused `src/recruitment_agent` scaffold

Description: The unused scaffold contains placeholder and `not_implemented` responses. It is not active, but it creates ambiguity and no-mock policy noise.

Affected files:

- `src/recruitment_agent/**`
- `Dockerfile`
- `pyproject.toml`

Acceptance criteria:

- Only one backend app tree is packaged and copied into the Docker image.
- No placeholder runtime endpoints remain in packaged code.

### P2-2: Runtime uploaded resume data is present in the repository

Description: `backend/data/resumes/...` contains a resume artifact. This is input data, not fake AI output, but runtime uploads should generally be ignored or moved to generated local storage.

Affected files:

- `backend/data/resumes/**`
- `.gitignore`

Acceptance criteria:

- Runtime upload directories are ignored.
- Any intentional test fixture is moved under `tests/fixtures`.
- README documents where local uploads are stored.

### P2-3: ORM relationships are sparse

Description: Many foreign keys do not have ORM relationships, which makes repository logic more manual and can hide cascade/ownership assumptions.

Affected files:

- `backend/app/db/models.py`

Acceptance criteria:

- Relationships are added where they clarify ownership and query behavior.
- Cascades are explicit and conservative.
- Tests cover deletes only if deletes are supported.

### P2-4: Validation schemas allow broad narrative recommendation fields

Description: Some LLM output schemas use free-form `str` for recommendations, while others use literals. This is why long recommendations were valid and revealed the old DB width bug.

Affected files:

- `backend/app/schemas/llm_outputs.py`
- prompt files under `backend/app/agents`

Acceptance criteria:

- Decide which outputs should be enum-like and which should be narrative.
- Add Pydantic length or enum constraints where appropriate.
- DB fields match the schema.

### P2-5: Test suite lacks integration markers and external dependency separation

Description: Unit tests pass, but integration tests for DB, Mailpit, LM Studio, and full API flow are absent.

Affected files:

- `tests/**`
- `pyproject.toml`

Acceptance criteria:

- Add markers such as `unit`, `db`, `mailpit`, `lmstudio`, and `e2e`.
- Unit tests do not require external services.
- Integration tests fail clearly when required local services are not running.

## Fixed During Audit

### FIXED-1: Interview evaluation persistence failed on long recommendation text

Description: `POST /api/v1/interviews/{session_id}/evaluate` returned HTTP 500 because `interview_evaluations.recommendation` was `VARCHAR(100)` and LM Studio returned a longer narrative recommendation. The same risk existed for final scorecards.

Affected files:

- `backend/app/db/models.py`
- `alembic/versions/20260622_0002_widen_llm_recommendations.py`

Acceptance criteria:

- `interview_evaluations.recommendation` is `Text`.
- `final_scorecards.recommendation` is `Text`.
- Alembic upgrades to `20260622_0002`.
- The full MVP flow reaches final human decision.
- Tests pass.

Status: complete.

### FIXED-2: Communication logs persisted raw interview tokens and OTPs

Description: Invite and OTP emails still send the real secret through SMTP/Mailpit, but `CommunicationLog.body` now stores explicit redactions instead of raw values. Metadata does not store the raw token or OTP.

Affected files:

- `backend/app/services/email.py`
- `backend/app/services/redaction.py`
- `backend/app/api/v1/interviews.py`
- `tests/unit/test_email_redaction.py`

Acceptance criteria:

- Invite log bodies contain `[REDACTED_INTERVIEW_TOKEN]`.
- OTP log bodies contain `[REDACTED_OTP]`.
- Raw token and OTP are absent from persisted communication body and metadata.
- SMTP delivery body remains unchanged.
- Tests pass.

Status: complete.

### FIXED-3: Recruiter/admin APIs were unauthenticated

Description: Added password-based login, Argon2 password hashes, JWT access tokens, FastAPI role dependencies, local dev-user seeding, and RBAC for recruiter/hiring-manager/admin APIs. Candidate interview-entry endpoints remain token/OTP based and public.

Affected files:

- `backend/app/api/deps.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/*.py`
- `backend/app/services/auth.py`
- `backend/app/repositories/users.py`
- `backend/app/schemas/auth.py`
- `backend/app/scripts/seed_dev_users.py`
- `backend/app/db/models.py`
- `alembic/versions/20260622_0003_add_user_auth_fields.py`
- `tests/unit/test_auth_security.py`

Acceptance criteria:

- Unauthenticated protected endpoints return `401`.
- Recruiter access to admin endpoints returns `403`.
- Admin users can access admin endpoints.
- Authenticated recruiter/hiring-manager users can perform allowed workflow actions.
- Human decisions use the authenticated user's `id`.
- Important audit logs include `actor_user_id`.
- Tests pass.

Status: complete.
