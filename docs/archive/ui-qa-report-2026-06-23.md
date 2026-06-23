# UI QA Report

## Phase 2C Update - 2026-06-23

Environment: Docker backend/PostgreSQL/Mailpit, Next.js dev server on `localhost:3000`, LM Studio on `host.docker.internal:1234/v1` from the backend container with `qwen/qwen3-4b-2507` loaded. `/health`, `/health/db`, and `/health/llm` returned `200`.

Full browser MVP flow result: **PASS with documented automation exceptions**. The in-app browser API does not expose a file-upload method, so the resume file transfer used the real protected backend upload endpoint with `tests/fixtures/resumes/jane_backend.txt`; the UI then processed, scored, shortlisted, planned, invited, interviewed, evaluated, generated the final scorecard, and submitted final decision with real backend/LM Studio calls. Mailpit token/OTP extraction used the real Mailpit API while the candidate actions were completed in the public browser UI.

Run IDs:

- Job: `224cc0a2-3551-4fe3-8693-b0a97f8b3e57`
- Candidate: `7f5e5913-d4a1-42e4-bd5d-9779fde8ec30`
- Interview session: `183c9fd5-5eee-4b07-8899-a4675973b12e`

Verified:

- Recruiter login works; protected `/jobs` redirects to `/login?next=%2Fjobs` without a token.
- Recruiter cannot use `/admin`; admin login can view LLM, audit, and communication logs.
- Job creation, JD calibration, criteria approval, candidate processing, score/evidence, shortlist, interview plan, invite, candidate OTP, chat interview completion, transcript, evaluation, final scorecard, and final human decision all completed with real local services.
- Candidate detail reload shows latest persisted score and interview session discovery with plan/evaluation links.
- Public candidate invalid token route renders a clear unavailable state without the protected shell.
- Completed candidate interview reload shows the completed state.
- Communication logs show redacted invite/OTP body content; raw invite token and OTP were not visible in the admin UI.

Fixes validated during this run:

- Frontend now reads persisted latest score through `GET /api/v1/candidates/{candidate_id}/score/latest`.
- Candidate/job candidate lists render latest score summaries from real `CandidateScore` rows.
- Candidate detail renders interview sessions from `GET /api/v1/candidates/{candidate_id}/interviews`.
- Interview invitation emails now use `FRONTEND_BASE_URL` for participant links like `/candidate/interview/{token}` instead of sending candidates to the backend JSON entry endpoint.
- Browser API calls now use `NEXT_PUBLIC_API_BASE_URL` directly, with backend CORS enabled for local frontend origins. This avoids long-running LM Studio mutations depending on the Next dev proxy.

Remaining limitations:

- Playwright E2E is still not configured. A slow real-flow E2E should remain gated behind `RUN_E2E=true` and require backend, Mailpit, PostgreSQL, and LM Studio.
- The in-app browser automation used here cannot attach local files to file inputs; human browser testing can use the upload UI directly.
- Voice/video interviews and coding assessments remain out of scope.

Phase 2B frontend route and contract audit for the Next.js UI Alpha.

Date: 2026-06-22

Scope:

- Frontend routes under `frontend/app`.
- Frontend API client calls in `frontend/src/lib/api.ts`.
- Backend route contracts in FastAPI route/schema files and OpenAPI.
- Focused frontend/backend unit tests and rendered browser smoke checks. Full live LM Studio browser flow remains manual because `/health/llm` returned `503` in this environment.

## Summary

| Route | Purpose | Result | Issues found | Screenshots | Fix status |
| --- | --- | --- | --- | --- | --- |
| `/login` | Recruiter/admin login | PASS AFTER FIX | Browser smoke found login failed with `Failed to execute 'fetch' on 'Window': Illegal invocation` because the API client stored an unbound browser `fetch`. The default fetcher now calls through a wrapper, and seeded recruiter login succeeds. | Browser capture emitted in session, not stored in repo | Fixed |
| `/` | Protected dashboard and health checks | PASS | Protected by `AuthShell`; redirects unauthenticated users to `/login?next=/`; backend/db health have loading/error states; LLM health is manual to avoid accidental slow LM Studio calls. | Not captured | No change |
| `/jobs` | Job list | PASS | Uses real `GET /api/v1/jobs`; has loading/error/empty states; no fake rows. | Not captured | No change |
| `/jobs/new` | Create job and optionally run calibration | PASS | Uses real create/calibrate endpoints; buttons disable during mutations; calibration shows long-running loading text. Form validation errors are shown through mutation error state. | Not captured | No change |
| `/jobs/[jobId]` | Job detail, criteria approval, upload, candidate summary | PASS | Uses real job/candidate endpoints; loading/error/empty states exist; process/calibrate/approve buttons disable during pending state. Candidate scores are not shown from list/detail because backend does not expose historical score records. | Not captured | Known backend limitation documented |
| `/jobs/[jobId]/candidates` | Candidate upload/list/process for a job | PASS | Uses real list/upload/process endpoints; loading/error/filter-empty states exist. Score/recommendation columns correctly avoid fake data and show not available unless backend exposes records. | Not captured | Known backend limitation documented |
| `/candidates/[candidateId]` | Candidate profile, score/evidence after process, shortlist, plan generation | PASS | Uses real candidate/process/shortlist/plan endpoints; process and plan show pending states; force processing requires confirmation; decision reason is required before submit. Score/evidence renders after the process response. | Not captured | No change |
| `/interviews/[sessionId]/plan` | Interview plan review/edit/invite send | PASS | Uses real session/plan/candidate/invite endpoints; loading/error/empty-per-question-type states exist; invite button disables while sending and Mailpit retrieval is explained. | Not captured | No change |
| `/candidate/interview/[token]` | Public candidate OTP and chat interview flow | PASS AFTER FIX | Public API calls do not attach JWT; OTP/start/answer/complete have clear pending states. Active interview refresh without restored turn previously showed the start button even though backend would reject it. Completed GET now returns completion state instead of a generic unavailable error. | Not captured | Fixed |
| `/interviews/[sessionId]/evaluation` | Transcript and interview evaluation | PASS | Uses real transcript/evaluation/evaluate endpoints; 409 no-evaluation state is handled as empty; `force=true` rerun requires confirmation; transcript empty state exists. | Not captured | No change |
| `/candidates/[candidateId]/final` | Final scorecard and final human decision | PASS | Uses real candidate/final-scorecard/final-decision endpoints; 409 no-scorecard state is handled as empty; `force=true` rerun requires confirmation; decision reason is required before submit. | Not captured | No change |
| `/admin` | Admin LLM/audit/communication logs | PASS AFTER FIX | Non-admin users see a frontend forbidden state and admin API calls are disabled. Backend enforces `ADMIN`. Communication logs previously omitted the persisted redacted body from the API/UI. | Not captured | Fixed |

## API Contract Findings

- Browser runtime login verified that the API client must not call an unbound `window.fetch`; `ApiClient` now wraps the default fetch call while preserving injected fetchers for tests.
- Protected frontend calls attach `Authorization: Bearer <token>` by default.
- Public candidate interview-entry calls explicitly pass `auth: false`; Vitest now covers the dedicated candidate methods, not only the generic request helper.
- `/api/v1/interview-entry/{token}/answer` and `/complete` include `client_session_nonce`; Vitest now asserts request bodies.
- `/api/v1/interviews/{sessionId}/evaluate?force=true` and `/api/v1/candidates/{candidateId}/final-scorecard?force=true` are used for forced reruns; Vitest now asserts the query strings.
- Backend `CommunicationLog` already persisted a redacted `body`, but `CommunicationLogRead` omitted it. The schema now exposes `body`, and `/admin` renders it with wrapping and overflow protection.
- `GET /api/v1/interview-entry/{token}` now allows completed sessions so the candidate UI can show a completion screen after reload.

## Auth/RBAC Findings

- `AuthShell` redirects protected pages without a token to `/login?next=<path>`.
- `ApiClient` clears the token and triggers login redirect on `401`.
- Admin navigation is only visible for `ADMIN`.
- Direct `/admin` access by non-admin users shows a forbidden UI state and avoids admin log queries.
- Backend tests already cover unauthenticated protected routes, recruiter denial for admin routes, and admin access.

Rendered browser smoke results:

- `/login` rendered with title `Recruitment Agent`, no framework overlay, and no console warnings/errors.
- Seeded recruiter login succeeded and landed on `/` with dashboard/current-user content.
- Recruiter dashboard did not expose admin navigation.
- Direct `/admin` as recruiter showed the frontend forbidden state.
- Seeded admin login succeeded and `/admin` rendered LLM usage, audit log, and communication log tabs.
- Logout followed by `/jobs` redirected to `/login?next=%2Fjobs`.
- `/candidate/interview/not-real-token` rendered the public interview-unavailable state without the recruiter login shell.

## Candidate UX Findings

- OTP sent, invalid OTP, expired token, missing/invalid nonce, and backend API errors surface through `ErrorState`.
- Start is only available after OTP verification.
- The start response stores `client_session_nonce` and the latest turn in `sessionStorage`.
- Answer and complete requests include `client_session_nonce`.
- Answer submit disables while pending and while the answer/nonce is missing.
- Active interview reload without a restored turn now shows a clear active-session recovery message instead of offering a start action that the backend will reject.
- Completion clears stored nonce/turn data after `/complete` succeeds.

## Recruiter/Admin UX Findings

- Long-running LM Studio actions display pending labels and disable repeated clicks: calibration, candidate processing, interview planning, invite send, interview evaluation, and final scorecard generation.
- Force rerun buttons require `window.confirm`.
- JSON fallback viewers use scrollable monospace blocks.
- Human decision buttons remain disabled until a reason is entered.
- Admin communication logs now display the redacted body and metadata with safe wrapping for long text.

## Remaining Limitations

- Historical score retrieval and interview discovery are fixed in Phase 2C.
- Full browser verification now passes with live PostgreSQL, Mailpit, seeded users, and LM Studio. No mock backend data or fake AI output was introduced.
