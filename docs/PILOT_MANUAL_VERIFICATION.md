# Pilot Manual Verification

Phase 4B is operational verification, not evaluation-quality testing. Do not run full LLM evals during this checklist. Use only `uv run python -m app.scripts.run_evals --dry-run-fixtures` to confirm fixture loading.

Use this checklist after Docker, PostgreSQL, Mailpit, backend, frontend, and LM Studio health checks are passing.

## Recruiter Or Admin

- [ ] Log in as a recruiter or admin.
- [ ] Open `/jobs/new`.
- [ ] Select a role template.
- [ ] Edit the raw JD before submitting.
- [ ] Create the job.
- [ ] Run calibration through real LM Studio.
- [ ] Review generated criteria and evidence guidance.
- [ ] Approve criteria as a human reviewer.
- [ ] Upload a candidate resume.
- [ ] Process the candidate through real LM Studio.
- [ ] Inspect persisted candidate score and evidence.
- [ ] Confirm unsupported or missing evidence is visible when present.
- [ ] Approve or hold/reject the shortlist decision with a reason.
- [ ] Generate the interview plan.
- [ ] Review fixed, resume-validation, soft-skill, knockout, and dynamic questions where present.
- [ ] Send the interview invite.

## Candidate

- [ ] Open Mailpit at `http://localhost:8025`.
- [ ] Open the invite link from Mailpit.
- [ ] Send OTP from the candidate interview page.
- [ ] Retrieve OTP from Mailpit.
- [ ] Verify OTP.
- [ ] Start interview.
- [ ] Answer all questions.
- [ ] Complete interview.
- [ ] Submit candidate feedback.

## Recruiter Or Admin Follow-Up

- [ ] View interview transcript.
- [ ] Evaluate interview through real LM Studio.
- [ ] Generate final scorecard through real LM Studio.
- [ ] Confirm final scorecard includes candidate, job, resume score, interview score, soft skill score, overall fit, risk level, evidence summary, missing evidence, recommendation, timestamp, and advisory disclaimer.
- [ ] Use `Print / Save as PDF`.
- [ ] Submit final decision with a reason.
- [ ] Submit scorecard feedback.
- [ ] Open admin page as an admin.
- [ ] Admin views feedback.
- [ ] Admin views LLM logs.
- [ ] Admin views audit logs.
- [ ] Admin views communication logs.
- [ ] Verify invite token and OTP are redacted in communication logs.

## Pass Criteria

- [ ] No mock LLM output was used.
- [ ] No fake AI result was created.
- [ ] No cloud LLM provider was called.
- [ ] Candidate interview token, OTP, and client-session nonce behavior worked.
- [ ] Human approvals were required for criteria, shortlist, and final decision.
- [ ] Pilot feedback was persisted and visible to admin users.
- [ ] Any failures are recorded in `docs/PILOT_VERIFICATION_STATUS.md`.
