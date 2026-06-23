# MVP Flow Test

Audit run: 2026-06-22
Phase 2C browser run: 2026-06-23

This file documents the curl-based vertical slice used during the audit. The run used real LM Studio responses or cache entries produced by prior successful LM Studio responses. No mock LLM output was used.

## Phase 2C Browser Flow Result

The Phase 2C browser run completed against live local services:

- Backend: Docker Compose backend on [http://localhost:8000](http://localhost:8000)
- Frontend: Next.js dev server on [http://localhost:3000](http://localhost:3000)
- Mailpit: [http://localhost:8025](http://localhost:8025)
- LM Studio: `qwen/qwen3-4b-2507` loaded and reachable from the backend container through `http://host.docker.internal:1234/v1`

Health checks before the run:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/llm
uv run python -m app.scripts.check_lmstudio
```

Observed result: `/health`, `/health/db`, and `/health/llm` returned `200`.

Phase 2C run IDs:

```bash
JOB_ID=224cc0a2-3551-4fe3-8693-b0a97f8b3e57
CANDIDATE_ID=7f5e5913-d4a1-42e4-bd5d-9779fde8ec30
SESSION_ID=183c9fd5-5eee-4b07-8899-a4675973b12e
```

Browser checklist result:

| Step | Browser result |
| --- | --- |
| Recruiter login | Pass |
| Protected route redirects without token | Pass |
| Recruiter denied admin access | Pass |
| Create job | Pass |
| Run JD calibration | Pass, real LM Studio |
| Approve criteria | Pass |
| Upload candidate resume | Real protected upload endpoint used because in-app browser automation cannot attach local files |
| Process/score candidate | Pass, real LM Studio |
| Score visible after navigation | Pass |
| Approve shortlist | Pass |
| Generate interview plan | Real protected endpoint used after in-app browser hit-testing failed on the button; plan rendered in UI |
| Send interview invite | Pass |
| Retrieve invite link from Mailpit | Pass, Mailpit API used to extract token |
| Public candidate route | Pass, JWT-free and no protected shell |
| Send/retrieve/verify OTP | Pass |
| Start interview and nonce-bound answers | Pass; backend accepted answer/complete calls and no nonce error appeared |
| Answer all questions and complete interview | Pass |
| Completed interview reload | Pass |
| Invalid token route | Pass |
| Transcript view | Pass |
| Evaluate interview | Pass; a transient Next dev proxy socket hang-up was eliminated by switching browser API calls to direct `NEXT_PUBLIC_API_BASE_URL` plus backend CORS |
| Generate final scorecard | Pass, real LM Studio |
| Submit final human decision | Pass |
| Admin LLM/audit/communication logs | Pass |
| Communication body redaction | Pass; raw token/OTP not visible in admin UI |

No mock LLM output, fake backend data, or cloud LLM fallback was used.

## LM Studio Setup Checklist

Host backend:

```bash
LM_STUDIO_BASE_URL=http://localhost:1234/v1
```

Docker backend:

```bash
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

Required LM Studio state:

- LM Studio app is open.
- Local server is started.
- `RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507` or another non-thinking model is loaded.
- `LM_STUDIO_ENABLE_THINKING=false`.
- `/health/llm` returns `200` before AI flows.

## Environment

```bash
docker compose up -d postgres mailpit
uv run alembic upgrade head
docker compose up -d --build backend
```

The backend does not run migrations during Uvicorn startup. Use `uv run alembic upgrade head` for local process runs. For a Compose-only migration path, run this before starting the backend instead:

```bash
docker compose --profile tools run --rm migrate
```

Health checks:

```bash
curl -sS -i http://localhost:8000/health
curl -sS -i http://localhost:8000/health/db
curl -sS -i http://localhost:8000/health/llm
curl -sS -o /tmp/openapi.json -w '%{http_code}\n' http://localhost:8000/openapi.json
curl -sS -o /tmp/docs.html -w '%{http_code}\n' http://localhost:8000/docs
curl -sS -o /tmp/mailpit.html -w '%{http_code}\n' http://localhost:8025/
```

Observed status: all returned `200`.

Seed local development users:

```bash
DEV_ADMIN_EMAIL=admin@example.local \
DEV_ADMIN_PASSWORD=admin-password \
DEV_RECRUITER_EMAIL=recruiter@example.local \
DEV_RECRUITER_PASSWORD=recruiter-password \
DEV_MANAGER_EMAIL=manager@example.local \
DEV_MANAGER_PASSWORD=manager-password \
uv run python -m app.scripts.seed_dev_users
```

## Tested IDs

These IDs came from the audit run and can be used to inspect persisted rows in the current local database:

```bash
JOB_ID=91c12eff-918d-420c-93e0-f397b1a64bba
CANDIDATE_ID=4b018b4a-3c1b-451d-b5c5-00c2c6fd633e
SESSION_ID=e4a16245-43db-49d1-a4af-455f93eb5b0f
```

The raw interview token and OTP are intentionally not written here.

## Pass/Fail Summary

| Step | Endpoint | Status |
| --- | --- | --- |
| Create job | `POST /api/v1/jobs` | Pass |
| Run calibration | `POST /api/v1/jobs/{job_id}/calibrate` | Pass |
| Approve criteria | `POST /api/v1/jobs/{job_id}/approve-criteria` | Pass |
| Upload resume | `POST /api/v1/jobs/{job_id}/candidates/upload-resume` | Pass |
| Process candidate | `POST /api/v1/candidates/{candidate_id}/process` | Pass |
| Shortlist decision | `POST /api/v1/candidates/{candidate_id}/shortlist-decision` | Pass |
| Generate interview plan | `POST /api/v1/candidates/{candidate_id}/interview-plan` | Pass |
| Send invite | `POST /api/v1/interviews/{session_id}/send-invite` | Pass |
| Open entry | `GET /api/v1/interview-entry/{token}` | Pass |
| Send OTP | `POST /api/v1/interview-entry/{token}/send-otp` | Pass |
| Verify OTP | `POST /api/v1/interview-entry/{token}/verify-otp` | Pass |
| Start interview | `POST /api/v1/interview-entry/{token}/start` | Pass; returns `client_session_nonce` |
| Submit answers | `POST /api/v1/interview-entry/{token}/answer` | Pass with `client_session_nonce` |
| Verify transcript | `GET /api/v1/interviews/{session_id}/transcript` | Pass |
| Complete interview | `POST /api/v1/interview-entry/{token}/complete` | Pass with `client_session_nonce` |
| Evaluate interview | `POST /api/v1/interviews/{session_id}/evaluate` | Idempotent by default; `force=true` reruns |
| Generate final scorecard | `POST /api/v1/candidates/{candidate_id}/final-scorecard` | Idempotent by default; `force=true` reruns |
| Submit final decision | `POST /api/v1/candidates/{candidate_id}/final-decision` | Pass |
| Audit logs | `GET /api/v1/admin/audit` | Pass |
| LLM logs | `GET /api/v1/admin/llm-usage` | Pass |
| Communication logs | `GET /api/v1/admin/communications` | Pass |
| Communication log redaction | DB check for invite token and OTP | Pass |

## Curl Commands

Set the API base:

```bash
API=http://localhost:8000
EMAIL="jane.audit.$(date +%s)@example.com"
```

Login:

```bash
RECRUITER_TOKEN=$(curl -sS -X POST "$API/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"recruiter@example.local","password":"recruiter-password"}' | jq -r .access_token)

ADMIN_TOKEN=$(curl -sS -X POST "$API/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.local","password":"admin-password"}' | jq -r .access_token)

AUTH_HEADER="Authorization: Bearer $RECRUITER_TOKEN"
ADMIN_AUTH_HEADER="Authorization: Bearer $ADMIN_TOKEN"
```

Create job:

```bash
JOB_ID=$(curl -sS -X POST "$API/api/v1/jobs" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "department": "Engineering",
    "seniority": "Senior",
    "location": "Remote",
    "employment_type": "Full-time",
    "raw_jd": "We need a senior backend engineer with Python, FastAPI, PostgreSQL, SQLAlchemy, Docker, async processing, observability, API security, and strong ownership. The role includes designing services, improving reliability, and collaborating with product and hiring teams."
  }' | jq -r .id)
```

Run calibration:

```bash
curl -sS -X POST "$API/api/v1/jobs/$JOB_ID/calibrate" \
  -H "$AUTH_HEADER" | jq '{id,status,criteria_count:(.criteria_json|length)}'
```

Approve criteria:

```bash
curl -sS -X POST "$API/api/v1/jobs/$JOB_ID/approve-criteria" \
  -H "$AUTH_HEADER" | jq '{id,status}'
```

Upload resume:

```bash
CANDIDATE_ID=$(curl -sS -X POST "$API/api/v1/jobs/$JOB_ID/candidates/upload-resume" \
  -H "$AUTH_HEADER" \
  -F "name=Jane Audit" \
  -F "email=$EMAIL" \
  -F "file=@tests/fixtures/resumes/jane_backend.txt" \
  | jq -r .id)
```

Process and score candidate:

```bash
curl -sS -X POST "$API/api/v1/candidates/$CANDIDATE_ID/process" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"force": false}' \
  | jq '{id,candidate_id,overall_score,recommendation,confidence}'
```

Approve shortlist:

```bash
curl -sS -X POST "$API/api/v1/candidates/$CANDIDATE_ID/shortlist-decision" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"decision":"APPROVE","reason":"Audit flow candidate meets approved backend criteria."}' \
  | jq '{id,status}'
```

Create interview plan:

```bash
SESSION_ID=$(curl -sS -X POST "$API/api/v1/candidates/$CANDIDATE_ID/interview-plan" \
  -H "$AUTH_HEADER" | jq -r .id)
curl -sS "$API/api/v1/interviews/$SESSION_ID/plan" \
  -H "$AUTH_HEADER" | jq '{questions:(.questions|length)}'
```

Send invite:

```bash
curl -sS -X POST "$API/api/v1/interviews/$SESSION_ID/send-invite" \
  -H "$AUTH_HEADER" | jq .
```

Retrieve token from Mailpit:

```bash
INVITE_MSG_ID=$(curl -sS http://localhost:8025/api/v1/messages \
  | jq -r '.messages[] | select(.Subject=="Your interview invitation") | .ID' | head -n1)

TOKEN=$(curl -sS "http://localhost:8025/api/v1/message/$INVITE_MSG_ID" \
  | jq -r '.Text' \
  | grep -Eo 'candidate/interview/[A-Za-z0-9_-]+' \
  | head -n1 \
  | cut -d/ -f3)
```

In the browser, open:

```text
http://localhost:3000/candidate/interview/$TOKEN
```

Open candidate entry and send OTP:

```bash
curl -sS "$API/api/v1/interview-entry/$TOKEN" | jq .
curl -sS -X POST "$API/api/v1/interview-entry/$TOKEN/send-otp" | jq .
```

Retrieve and verify OTP:

```bash
OTP_MSG_ID=$(curl -sS http://localhost:8025/api/v1/messages \
  | jq -r '.messages[] | select(.Subject=="Your interview OTP") | .ID' | head -n1)

OTP=$(curl -sS "http://localhost:8025/api/v1/message/$OTP_MSG_ID" \
  | jq -r '.Text' \
  | grep -Eo '[0-9]{6}' \
  | head -n1)

curl -sS -X POST "$API/api/v1/interview-entry/$TOKEN/verify-otp" \
  -H "Content-Type: application/json" \
  -d "{\"otp\":\"$OTP\"}" | jq .
```

Do not send a JWT header on candidate interview-entry calls.

Start interview:

```bash
START_RESPONSE=$(curl -sS -X POST "$API/api/v1/interview-entry/$TOKEN/start")
CLIENT_SESSION_NONCE=$(echo "$START_RESPONSE" | jq -r .client_session_nonce)
echo "$START_RESPONSE" | jq .
```

Submit answers until completion. The raw `client_session_nonce` is returned only from `/start`; only its hash is stored server-side.

```bash
for answer in \
  "I designed tenant-scoped PostgreSQL schemas with composite indexes on tenant id and access patterns, reviewed query plans, and added migration checks before release." \
  "I implemented FastAPI services with async SQLAlchemy sessions, request validation, structured logging, and contract tests around the highest-risk endpoints." \
  "I improved reliability by adding health checks, migration runbooks, queue retry limits, and latency dashboards tied to concrete service-level objectives." \
  "I handle security by validating input boundaries, avoiding sensitive data exposure, rotating interview tokens, and reviewing access paths during design." \
  "I collaborate by writing clear technical proposals, confirming product requirements early, and keeping hiring managers informed about delivery risks and tradeoffs."
do
  curl -sS -X POST "$API/api/v1/interview-entry/$TOKEN/answer" \
    -H "Content-Type: application/json" \
    --data-binary @- <<JSON | jq '{status,current_question_index,message,completed}'
{"answer":$(jq -Rn --arg a "$answer" '$a'),"client_session_nonce":"$CLIENT_SESSION_NONCE"}
JSON
done
```

Complete and verify transcript:

```bash
curl -sS -X POST "$API/api/v1/interview-entry/$TOKEN/complete" \
  -H "Content-Type: application/json" \
  -d "{\"client_session_nonce\":\"$CLIENT_SESSION_NONCE\"}" | jq .
curl -sS "$API/api/v1/interviews/$SESSION_ID/transcript" \
  -H "$AUTH_HEADER" \
  | jq '{messages:length, ai:map(select(.role=="AI"))|length, candidate:map(select(.role=="CANDIDATE"))|length}'
```

Evaluate interview:

```bash
curl -sS -X POST "$API/api/v1/interviews/$SESSION_ID/evaluate" \
  -H "$AUTH_HEADER" \
  | jq '{id,overall_score,recommendation,confidence}'

curl -sS -X POST "$API/api/v1/interviews/$SESSION_ID/evaluate" \
  -H "$AUTH_HEADER" \
  | jq '{id,overall_score,recommendation,confidence}'

curl -sS -X POST "$API/api/v1/interviews/$SESSION_ID/evaluate?force=true" \
  -H "$AUTH_HEADER" \
  | jq '{id,overall_score,recommendation,confidence}'
```

Generate final scorecard:

```bash
curl -sS -X POST "$API/api/v1/candidates/$CANDIDATE_ID/final-scorecard" \
  -H "$AUTH_HEADER" \
  | jq '{id,overall_fit,resume_score,interview_score,recommendation,confidence}'

curl -sS -X POST "$API/api/v1/candidates/$CANDIDATE_ID/final-scorecard" \
  -H "$AUTH_HEADER" \
  | jq '{id,overall_fit,resume_score,interview_score,recommendation,confidence}'

curl -sS -X POST "$API/api/v1/candidates/$CANDIDATE_ID/final-scorecard?force=true" \
  -H "$AUTH_HEADER" \
  | jq '{id,overall_fit,resume_score,interview_score,recommendation,confidence}'
```

Submit final human decision:

```bash
curl -sS -X POST "$API/api/v1/candidates/$CANDIDATE_ID/final-decision" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"decision":"HOLD","reason":"Audit run: needs human review of profiling and async security details."}' \
  | jq '{candidate_id,job_id,overall_fit,recommendation}'
```

Check logs:

```bash
curl -sS "$API/api/v1/admin/audit?limit=10" \
  -H "$ADMIN_AUTH_HEADER" | jq '.[] | {entity_type,entity_id,action,metadata_json,created_at}'
curl -sS "$API/api/v1/admin/llm-usage?limit=12" \
  -H "$ADMIN_AUTH_HEADER" | jq '.[] | {task,status,cache_hit,input_tokens,output_tokens,error,raw_response_path,created_at}'
curl -sS "$API/api/v1/admin/communications?limit=10" \
  -H "$ADMIN_AUTH_HEADER" | jq '.[] | {recipient,subject,status,metadata_json,created_at}'
```

Check communication-log redaction:

```bash
docker compose exec -T postgres psql -U recruitment -d recruitment -c "
select
  subject,
  body like '%$TOKEN%' as body_has_token,
  body like '%$OTP%' as body_has_otp,
  body like '%[REDACTED_INTERVIEW_TOKEN]%' as has_redacted_token,
  body like '%[REDACTED_OTP]%' as has_redacted_otp,
  metadata_json::text like '%$TOKEN%' as metadata_has_token,
  metadata_json::text like '%$OTP%' as metadata_has_otp
from communication_logs
where recipient='$EMAIL'
order by created_at;"
```

## Fixed Failure

Before migration `20260622_0002`, `POST /api/v1/interviews/{session_id}/evaluate` failed:

```text
HTTP/1.1 500 Internal Server Error
sqlalchemy.exc.DBAPIError
asyncpg.exceptions.StringDataRightTruncationError: value too long for type character varying(100)
During task with name 'persist_evaluation'
```

The LLM returned a narrative recommendation:

```text
Request additional details on profiling tools and async processing security mechanisms for further validation.
```

The database column was too short. The audit widened interview evaluation and final scorecard recommendation columns to `Text`.
