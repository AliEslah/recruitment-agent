# Phase 3B Eval Triage Report

## Run Context

- Date: 2026-06-23
- Model: `qwen/qwen3-4b-2507`
- LM Studio base URL: `http://localhost:1234/v1`
- Primary baseline report: `evals/reports/20260623T100907Z_eval_report.json`
- Final after-fix report: `evals/reports/20260623T104144Z_eval_report.json`
- Job families evaluated: backend engineering, customer support, finance, HR, marketing, operations, sales

Final prompt versions:

- `job_calibration`: `job-calibration-v2`
- `resume_parsing`: `resume-parsing-v3`
- `candidate_scoring`: `candidate-scoring-v4`
- `interview_planning`: `interview-planning-v2`
- `interview_evaluation`: `interview-evaluation-v4`
- `final_scorecard`: `final-scorecard-v2`

## Execution Summary

The first real full run with LM Studio passed infrastructure but exposed a schema-quality blocker in an earlier run: resume parsing returned `null` for list fields. The schema and prompt were updated so absent scalar fields use `null` while absent list fields use `[]`, and schemas tolerate `null` list values as absent lists.

Baseline full run after the schema fix:

- Report: `20260623T100907Z_eval_report.json`
- Status: passed
- Stage results: 30 passed, 12 failed
- Summary score: 0.714
- Unsupported evidence items: 36
- Weakly grounded evidence items: 14
- Protected-term warnings: 0

Final full run after targeted fixes:

- Report: `20260623T104144Z_eval_report.json`
- Status: passed
- Runtime: 201 seconds
- LLM calls: 49 total, 42 cache hits, 7 uncached calls
- Stage results: 39 passed, 3 failed
- Summary score: 0.929
- Unsupported evidence items: 3
- Weakly grounded evidence items: 6
- Protected-term warnings: 0

## Stage Summary

Final full run by stage:

- Job calibration: 7 passed, 0 failed
- Resume parsing: 7 passed, 0 failed
- Candidate scoring: 5 passed, 2 failed
- Interview planning: 7 passed, 0 failed
- Interview evaluation: 6 passed, 1 failed
- Final scorecard: 7 passed, 0 failed

Targeted before/after:

- Candidate scoring improved from 0/7 after the first calibration prompt change to 5/7 after `candidate-scoring-v4` plus evidence-check fixes.
- Interview evaluation improved from 0/7 to 6/7 after transcript-only evidence wording and narrower grounding checks.
- Final scorecard passed 7/7 after upstream candidate/interview fixes.

## Top Quality Problems

1. Candidate scoring still over-recommends in some cases.
   - Operations remains `STRONG_MATCH` while the fixture expected band is `POSSIBLE_MATCH`.
   - Customer support and sales still fail because one evidence item is unsupported.

2. Interview evaluation still has one transcript-grounding failure.
   - Customer support evaluation includes an evidence summary that blends transcript content with resume-like workflow claims.

3. Score-to-band calibration is not fully aligned with missing evidence.
   - HR and marketing correctly moved to `POSSIBLE_MATCH`, but the generic score-band helper still warns because scores are 88 and 89.
   - This indicates the helper thresholds should be calibrated separately from prompt behavior.

4. Interview planning has a minor coverage issue.
   - Backend engineer interview plan missed a `SOFT_SKILL` question type, though the stage passed because this is report-only.

## Evidence Grounding Warnings

Final unsupported evidence examples, summarized:

- Customer support candidate scoring inferred calm empathetic tone from CSAT and follow-up rather than quoting direct resume evidence.
- Sales candidate scoring inferred joint handoff and expansion case-study work that was not present in the resume text.
- Customer support interview evaluation summarized customer handling in a way that had low token overlap with the transcript and appears to mix in non-transcript support workflow claims.

Weak grounding remains for some legitimate paraphrases, especially operations and sales interview evaluations. This is expected with token-overlap heuristics and should be reviewed manually before changing prompts.

## Protected-Term Warnings

No protected-attribute warnings remain in the final report. A targeted candidate-scoring rerun briefly flagged `single` in a technical phrase (`single API call`); the protected-term scanner now requires marital/family context for `single`.

## Consistency Warnings

The final report contains 40 `needs_validation` warnings. These are expected report-only signals where resume skills were not validated in transcripts, such as:

- Engineering: Python, FastAPI, PostgreSQL
- Support: Zendesk and help center documentation
- Finance: Excel modeling, forecasting, stakeholder reporting
- Sales: negotiation and pipeline generation

These are useful follow-up validation signals, not eval execution failures.

## Schema And Validation Failures

Resolved P0:

- `ParsedResumeOutput` rejected `null` for list fields (`education`, `certifications`, `projects`, `links`).
- Fix: `resume-parsing-v3` instructs `[]` for absent list fields, and list fields normalize `null` to empty lists.

No schema failures remain in the final full run.

## Roles Where Scoring Is Weakest

- Customer support: candidate scoring and interview evaluation both still fail evidence grounding.
- Sales account executive: candidate scoring still fails evidence grounding despite interview and final scorecard passing.
- Operations manager: recommendation remains stronger than fixture expectation.

## Stages Where Output Is Weakest

- Candidate scoring is the weakest stage: 5/7 pass, with remaining unsupported evidence and over-strong recommendation risk.
- Interview evaluation is next: 6/7 pass, with one remaining transcript-grounding failure.
- Final scorecard is currently strongest among decision stages: 7/7 pass, though it carries validation warnings forward.

## Applied Fixes

- Set and documented exact LM Studio eval env requirements.
- Changed resume parsing prompt to distinguish scalar `null` from list `[]`.
- Added schema normalization for `null` list values.
- Tightened candidate scoring prompt to avoid `STRONG_MATCH` when material validation gaps remain.
- Tightened interview evaluation prompt to require transcript-only evidence and keep missing validation out of `red_flags`.
- Improved evidence checks so candidate-score concerns are not treated as evidence and interview strengths/weaknesses do not create unsupported-evidence failures.
- Refined protected-term scanner to avoid false positives for technical uses of `single`.
- Added report runtime and cache-hit metadata.
- Added stage-level recommendation distribution.

## Recommended Next Fixes

1. Add stronger source-span discipline for candidate scoring evidence.
2. Tune score-to-band helper thresholds or make them gap-aware.
3. Add report-only expected-band checks for interview/final outputs when a canonical band exists.
4. Improve interview planning prompt to force one explicit soft-skill question in every plan.
5. Add progress logging in the eval runner so long LM Studio runs show role/stage progress.

## Phase 3C-Lite Update

Final Phase 3C-Lite consolidated report:

- Report: `evals/reports/20260623T111250Z_eval_report.json`
- Status: passed
- Model: `qwen/qwen3-4b-2507`
- Runtime: 337 seconds
- LLM calls: 49 total, 35 cache hits, 14 uncached calls
- Stage results: 42 passed, 0 failed
- Summary score: 1.0
- Unsupported evidence items: 0
- Protected-attribute warnings: 0

Prompt versions after Phase 3C-Lite:

- `candidate_scoring`: `candidate-scoring-v6`
- `interview_evaluation`: `interview-evaluation-v7`
- Other prompt versions unchanged from Phase 3B.

Resolved Phase 3B failures:

- Customer support candidate-scoring evidence now uses resume facts rather than inferred tone.
- Sales account executive candidate-scoring evidence no longer invents handoff case-study work.
- Customer support interview evaluation now uses transcript-only evidence and moves ticket speed, SLA, Zendesk, and help-center gaps to missing evidence or consistency warnings.

No new eval failures were introduced. Remaining risks are report-only:

- Recommendation calibration warnings still exist where `POSSIBLE_MATCH` is paired with high numeric scores, or fixture expected bands differ from model output.
- `risks_empty` appears for two high-scoring candidate-score outputs and should be monitored.
- `needs_validation` consistency warnings remain useful signals for follow-up interview coverage.
- One resume parsing warning remains for `copywriting` due token-overlap limits.

Recommendation: proceed to Phase 4 Pilot Readiness. Keep the report-only warnings visible and address score-band calibration, fixture breadth, progress logging, and interview-plan soft-skill coverage during pilot hardening.
