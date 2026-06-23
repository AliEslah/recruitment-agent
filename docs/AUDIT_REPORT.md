# Technical Audit Report

Audit date: 2026-06-22

## Scope

This audit reviewed the current FastAPI + LangGraph + LM Studio recruiting MVP. The goal was to run, verify, and stabilize the existing implementation without adding product features, replacing the stack, or adding fake LLM behavior.

## P0 Security Update

After the initial audit, the P0 security pass fixed the two open blockers:

- Communication logs now redact raw interview tokens as `[REDACTED_INTERVIEW_TOKEN]` and raw OTPs as `[REDACTED_OTP]` before persistence.
- Recruiter, hiring-manager, and admin APIs now require JWT authentication and role checks. Candidate interview-entry endpoints remain token/OTP based and public.

The current reliability migration head after Phase 1B cleanup is `20260622_0005`. See `docs/ISSUES_PHASE_1B.md` for the superseding reliability and cleanup status.

## Architecture Summary

- Active backend: `backend/app`, imported as `app` through `pyproject.toml` `pythonpath = ["backend"]`.
- FastAPI entrypoint: `backend/app/main.py`, with `create_app()` including health routes and `/api/v1`.
- API routers: `backend/app/api/v1/{jobs,candidates,interviews,decisions,admin,health}.py`.
- Database: async SQLAlchemy models in `backend/app/db/models.py`, async engine/session in `backend/app/core/database.py`.
- Migrations: Alembic in `alembic/`; initial migration uses `Base.metadata.create_all()`. Later revisions include `20260622_0002_widen_llm_recommendations.py`, `20260622_0003_add_user_auth_fields.py`, `20260622_0004_reliability_indexes_nonce.py`, and `20260622_0005_chat_only_interview_mode.py`.
- LLM integration: `backend/app/services/lmstudio.py` uses `openai.AsyncOpenAI` against LM Studio's local OpenAI-compatible API.
- Structured JSON validation/cache/logging: `backend/app/services/llm_json.py` validates with Pydantic schemas in `backend/app/schemas/llm_outputs.py`, caches successful outputs, and writes `LlmCallLog`.
- Email: `backend/app/services/email.py` sends through SMTP, verified with Mailpit.
- Token/OTP security: `backend/app/services/tokens.py`, `backend/app/services/otp.py`, plus interview session fields.
- LangGraph workflows: implemented under `backend/app/agents`.
- Cleanup: the unused `src/recruitment_agent` tree was deleted; the Docker image and package target use only `backend/app`.

## Runtime Verification

Commands used:

```bash
docker compose up -d postgres mailpit
docker compose ps
uv run alembic upgrade head
docker compose logs --no-color --tail=120 backend
curl -sS -i http://localhost:8000/health
curl -sS -i http://localhost:8000/health/db
curl -sS -i http://localhost:8000/health/llm
curl -sS -o /tmp/openapi.json -w '%{http_code}\n' http://localhost:8000/openapi.json
curl -sS -o /tmp/docs.html -w '%{http_code}\n' http://localhost:8000/docs
uv run pytest -q
docker compose up -d --build backend
```

Results:

- Docker Compose services: PostgreSQL, Mailpit, and backend are running.
- PostgreSQL: reachable; `/health/db` returns `200`.
- Mailpit: reachable at `http://localhost:8025`, returned `200`.
- Backend: starts and serves `AI Recruiting Decision Platform`.
- Migrations: applied cleanly to `20260622_0002 (head)`.
- OpenAPI: `/openapi.json` returns `200` with 33 paths.
- Swagger: `/docs` returns `200`.
- Tests: `21 passed, 1 warning`.

Important deployment gap: the backend container starts Uvicorn only. It does not run migrations automatically. New environments require a separate `uv run alembic upgrade head` step.

## LM Studio Status

Configuration surface:

- `LM_STUDIO_BASE_URL`
- `LM_STUDIO_API_KEY`
- `RECRUITING_LLM_MODEL`
- `RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON`
- `LM_STUDIO_TEMPERATURE`
- `LM_STUDIO_TIMEOUT_SECONDS`
- `LM_STUDIO_MAX_TOKENS`
- `LM_STUDIO_ENABLE_THINKING`

Verified behavior:

- `/health/llm` performed a real tiny local model call and returned `200`.
- Simulated unreachable LM Studio with:

```bash
LM_STUDIO_BASE_URL=http://127.0.0.1:9/v1 \
RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507 \
LM_STUDIO_API_KEY=lm-studio \
uv run python - <<'PY'
import asyncio
from app.services.lmstudio import LMStudioClient
from app.core.errors import AppError

async def main():
    try:
        await LMStudioClient().health_check()
    except AppError as exc:
        print(type(exc).__name__)
        print(exc.status_code)
        print(exc.message)

asyncio.run(main())
PY
```

Output was `LLMUnavailableError`, `503`, and `LM Studio is not reachable. Start LM Studio local server and load the configured model.`

No cloud fallback or mock fallback was found in the active backend. Thinking-only model IDs are blocked by default for structured JSON.

Phase 1B update:

- `/health/llm` is logged as task `health.llm` with `cache_hit=false`.
- `LlmCallLog.input_tokens` and `output_tokens` are populated when LM Studio returns usage fields and left `NULL` when missing.
- `estimated_cost` remains `NULL`; no local pricing strategy is defined.
- Validation failures write the last raw invalid response to disk, but successful raw responses are not retained.

## LangGraph Implementation Status

All required workflows are implemented as `langgraph.graph.StateGraph`.

| Graph | File | State | Nodes | Edges/Exit | Persistence | LLM/Pydantic | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `JobCalibrationGraph` | `backend/app/agents/job_calibration/graph.py` | `JobCalibrationState` | `load_job`, `improve_jd`, `extract_hiring_rubric`, `normalize_criteria_weights`, `validate_rubric`, `persist_results` | Linear `START -> ... -> END` | Updates `jobs` with improved JD, criteria, status | LM Studio through `LLMJsonService`; `JDImprovementOutput`, `HiringRubricOutput` | Implemented and verified |
| `CandidateProcessingGraph` | `backend/app/agents/candidate_processing/graph.py` | `CandidateProcessingState` | `load_candidate_and_job`, `extract_resume_text`, `parse_resume`, `extract_links`, `build_enriched_profile`, `score_candidate`, `apply_basic_rules`, `persist_candidate_results` | Linear `START -> ... -> END` | Updates candidate profile/status and inserts `CandidateScore` | LM Studio through `LLMJsonService`; `ParsedResumeOutput`, `CandidateScoreOutput` | Implemented and verified |
| `InterviewPlanningGraph` | `backend/app/agents/interview/planning_graph.py` | `InterviewPlanningState` | `load_context`, `generate_interview_plan`, `validate_interview_plan`, `persist_interview_plan`, `create_interview_session` | Linear `START -> ... -> END` | Creates `InterviewSession` with plan | LM Studio through `LLMJsonService`; `InterviewPlanOutput` | Implemented; `persist_interview_plan` is a no-op |
| `LiveInterviewGraph` | `backend/app/agents/interview/live_graph.py` | `LiveInterviewState` | `verify_session_security`, `load_interview_state`, `record_candidate_answer_if_present`, `decide_next_action`, `maybe_generate_follow_up`, `get_next_question`, `persist_turn_state`, `complete_if_finished` | Conditional after follow-up decision; exits at `END` | Writes transcript messages, graph state, session status, candidate status | Follow-up generation uses LM Studio and `FollowUpDecisionOutput`; normal question progression is deterministic from plan | Implemented and verified |
| `InterviewEvaluationGraph` | `backend/app/agents/interview/evaluation_graph.py` | `InterviewEvaluationState` | `load_completed_interview`, `validate_transcript`, `evaluate_interview`, `check_resume_interview_consistency`, `validate_evaluation`, `persist_evaluation` | Linear `START -> ... -> END` | Inserts `InterviewEvaluation` | LM Studio through `LLMJsonService`; `InterviewEvaluationOutput` | Implemented and verified after schema fix; consistency check is a no-op |
| `FinalDecisionGraph` | `backend/app/agents/final_decision/graph.py` | `FinalDecisionState` | `load_full_candidate_context`, `generate_final_scorecard`, `validate_final_scorecard`, `persist_final_scorecard` | Linear `START -> ... -> END` | Inserts `FinalScorecard` | LM Studio through `LLMJsonService`; `FinalScorecardOutput` | Implemented and verified |

No LangGraph checkpointer is configured. DB persistence happens inside graph nodes.

## Database Status

Required entities exist:

- `User`
- `Job`
- `Candidate`
- `CandidateScore`
- `InterviewSession`
- `InterviewMessage`
- `InterviewEvaluation`
- `FinalScorecard`
- `HumanDecision`
- `CommunicationLog`
- `AuditLog`
- `LlmCallLog`
- `QuestionBankItem`

Enums exist for user role, job status, candidate status, interview mode/status/message role, human decision stage/value, and security events.

JSON/JSONB fields are used for criteria, parsed profiles, score evidence, interview plans, graph state, security events, logs metadata, cache output, and score details.

Indexes/constraints currently include primary keys, unique `users.email`, unique `interview_sessions.secure_token_hash`, and unique `llm_cache.input_hash`. Missing indexes on common query paths include candidate/job lookups, score recency lookups, interview messages by session/time, logs by created time, and LLM log query filters.

Relationships are minimal. `Job.candidates` and `Candidate.job` are defined; most other foreign keys do not have ORM relationships.

## MVP API Flow Status

The full flow was exercised with curl against the running backend and real LM Studio:

1. Create job: pass
2. Run job calibration: pass
3. Approve criteria: pass
4. Add candidate/upload resume: pass
5. Resume parsing: pass
6. Candidate scoring: pass
7. Human shortlist decision: pass
8. Generate interview plan: pass
9. Send invite: pass
10. Candidate entry: pass
11. Send OTP: pass
12. Verify OTP: pass
13. Start interview: pass
14. Submit answers until completion: pass
15. Verify transcript saved: pass, 10 messages, 5 AI and 5 candidate
16. Evaluate interview: initially failed with HTTP 500, then passed after migration `20260622_0002`
17. Generate final scorecard: pass
18. Submit final human decision: pass
19. Audit logs: pass
20. LLM usage logs: pass
21. Communication logs: pass

Initial failure:

- Endpoint: `POST /api/v1/interviews/{session_id}/evaluate`
- Expected: persisted `InterviewEvaluation`
- Actual: HTTP 500, `StringDataRightTruncationError`
- Cause: `interview_evaluations.recommendation` was `VARCHAR(100)` while the Pydantic schema allows narrative text.
- Fix applied: widened `interview_evaluations.recommendation` and `final_scorecards.recommendation` to `Text`.

## Security Status

Verified:

- Interview token stored as SHA-256 hash on `InterviewSession`.
- Raw token is not stored in `interview_sessions.secure_token_hash`.
- OTP stored as salted PBKDF2 hash.
- OTP expiration is checked.
- Interview token expiration is checked.
- Interview cannot start before OTP verification.
- Interview cannot continue after completion through candidate entry endpoints.
- Security events are appended for token open, OTP sent, OTP verified, session started, and session completed.
- Candidate interview entry response does not expose token hash, OTP hash, recruiter/admin logs, or score details.

Important gaps:

- `single_session_lock` prevents a second `/start` call while active, but `/answer` accepts the token without proving the same browser/session lock.
- Status transitions are enforced in some places but not centralized.

## No-Mock Policy

Active backend findings:

- No runtime mock LLM output found.
- No fake AI fallback found.
- No cloud LLM fallback found.
- `LLMJsonService` only caches successfully parsed LM Studio outputs.
- Email is sent through SMTP and verified with Mailpit.

Phase 1B repository cleanup:

- `src/recruitment_agent` was deleted and is not copied into the Docker image.
- The old `LM_STUDIO_MODEL` fallback, unused reasoning-model setting, and unimplemented `VOICE`/`VIDEO` interview modes were removed.
- Runtime resume uploads are ignored under `backend/data/resumes/`.
- The intentional resume fixture was moved to `tests/fixtures/resumes/jane_backend.txt`.

## LLM Logging And Caching

Verified:

- Workflow LLM calls create `LlmCallLog` rows.
- Logs include task name, model name, latency, status, cache hit flag, error, and raw failure path.
- Cache hits are logged.
- Cache entries are written only after successful validation.

Phase 1B update:

- `/health/llm` is logged.
- Token counts are populated when returned by LM Studio and otherwise left `NULL`.
- Indexes were added for `(task, status, created_at)` and `input_hash`.
- Successful raw responses are not saved, which limits traceability.

## Test Status

Command:

```bash
uv run pytest -q
```

Result:

```text
21 passed, 1 warning
```

Covered:

- health route shape
- route presence in OpenAPI
- config defaults and overrides
- thinking-model guard
- token hash/verify
- OTP hash/verify
- interview expiration helper
- cache key generation
- criteria weight normalization
- JSON extraction helper
- basic import and infrastructure file checks

Gaps:

- No DB-backed integration tests.
- No Alembic migration test.
- No full API flow test.
- No Mailpit/SMTP integration test.
- No LM Studio integration test marker.
- No tests for LLM logging rows, cache rows, validation failure logging, status transitions, or security event persistence.

## Minimal Fixes Applied

- Added `alembic/versions/20260622_0002_widen_llm_recommendations.py`.
- Updated `backend/app/db/models.py` so `InterviewEvaluation.recommendation` and `FinalScorecard.recommendation` use `Text`.
- Applied the migration.
- Rebuilt the backend container.
- Re-ran tests and health checks.
