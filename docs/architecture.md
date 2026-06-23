# Architecture

The system is a local-first recruiting decision-support MVP. It combines a FastAPI backend, PostgreSQL persistence, LangGraph workflow orchestration, LM Studio local inference, and a Next.js frontend.

## Runtime Components

- `backend/app/main.py`: FastAPI application entrypoint.
- `backend/app/api/v1`: REST routes for auth, jobs, candidates, interviews, decisions, admin logs, and health.
- `backend/app/agents`: LangGraph workflows for job calibration, candidate processing, interview planning, live interviews, interview evaluation, and final decisions.
- `backend/app/services`: LM Studio client, JSON LLM wrapper, email delivery, file handling, token/OTP handling, redaction, and auth helpers.
- `backend/app/db`: SQLAlchemy models and async database session setup.
- `alembic/`: schema migrations.
- `frontend/`: Next.js App Router frontend.
- `evals/`: synthetic evaluation fixtures and reports.

## Data Flow

1. A recruiter creates a job from a raw job description.
2. `JobCalibrationGraph` produces improved job content and weighted criteria.
3. A human reviewer edits and approves the criteria.
4. A recruiter uploads a resume. The backend extracts text without using an LLM.
5. `CandidateProcessingGraph` parses and scores the candidate against approved criteria.
6. A human reviewer submits a shortlist decision.
7. `InterviewPlanningGraph` creates an interview plan.
8. The backend sends an invite through SMTP/Mailpit and protects candidate entry with token, OTP, and client-session nonce boundaries.
9. `LiveInterviewGraph` runs the chat interview one turn at a time.
10. `InterviewEvaluationGraph` evaluates the transcript.
11. `FinalDecisionGraph` produces a scorecard, and a human reviewer submits the final decision.

## Local LLM Boundary

The backend calls LM Studio through its OpenAI-compatible local API. The `openai` package is a protocol client, not a cloud-provider dependency in this project. There is no cloud LLM fallback.

## Persistence And Logs

PostgreSQL stores jobs, criteria, candidates, extracted resume text, scores, interview sessions, messages, final scorecards, users, audit logs, communication logs, and LLM logs. Communication logs redact delivery secrets before persistence.

Runtime uploads are written under ignored local storage and must not be committed. Synthetic fixtures under `tests/fixtures` and `evals/fixtures` are intentionally safe for public review.
