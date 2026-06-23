# Phase 3C-Lite Quality Issues

## Summary

- Previous consolidated result: 39/42 passed, summary score 0.929.
- New consolidated result: 42/42 passed, summary score 1.0.
- Final report: `evals/reports/20260623T111250Z_eval_report.json`.
- Protected-attribute warnings: 0.
- Unsupported evidence failures: 0.
- Mock or fake LLM output: none.
- Fixture expected notes changed: no.

## Resolved Issues

### RESOLVED P1-001 Customer Support Candidate Scoring Used Inferred Tone As Evidence

- Stage: candidate scoring
- Affected area: `candidate-scoring-v6`
- Previous example: evidence included `Calm, empathetic communication under pressure`, which was an inference rather than a resume fact.
- Fix: prompt now forbids standalone inferred trait phrases such as calm, empathetic, proactive, strong, proven, or under pressure as evidence.
- Result: customer-support candidate scoring passes evidence grounding in `20260623T105540Z_eval_report.json` and final full report.
- Acceptance criteria: candidate-scoring evidence remains source-grounded and concerns/inferences are not treated as hard evidence.

### RESOLVED P1-002 Sales Candidate Scoring Invented Handoff Case-Study Evidence

- Stage: candidate scoring
- Affected area: `candidate-scoring-v6`
- Previous example: evidence included `Joint work in handoff processes and expansion case studies implied`.
- Fix: prompt now requires each evidence string to quote or directly summarize resume/profile facts and move indirect support to concerns or risks.
- Result: sales candidate scoring passes evidence grounding in `20260623T105540Z_eval_report.json` and final full report.
- Acceptance criteria: unsupported handoff or expansion case-study claims are no longer emitted as evidence.

### RESOLVED P1-003 Customer Support Interview Evaluation Mixed Resume Context Into Transcript Evidence

- Stage: interview evaluation
- Affected area: `interview-evaluation-v7`, interview evidence grounding helper
- Previous example: evidence blended transcript answers with ticket volume, Zendesk, and workflow claims that were not said in the interview transcript.
- Fix: prompt now requires evidence as 2-4 short transcript-only quote/summary items and forbids criterion-named evidence entries for undiscussed criteria. The grounding helper checks interview evidence dictionary values separately when dictionaries are returned.
- Result: customer-support interview evaluation passes evidence grounding in `20260623T110716Z_eval_report.json` and final full report.
- Acceptance criteria: red flags and soft-skill scores are grounded in actual candidate answers, while Zendesk/help-center gaps remain consistency warnings.

## Remaining Report-Only Issues

### P1-004 Score-Band Helper Is Still Too Coarse

- Stage: candidate scoring
- Affected area: `check_recommendation_band`
- Example: high numeric scores with `POSSIBLE_MATCH` still trigger `recommendation_score_mismatch`.
- Expected behavior: band consistency should consider missing evidence and risks, not only numeric score thresholds.
- Acceptance criteria: helper emits calibrated warnings that distinguish score inconsistency from justified gap-aware `POSSIBLE_MATCH`.

### P1-005 Fixture Expected Bands Still Differ For Some Strong Outputs

- Stage: candidate scoring
- Affected area: fixture comparison/reporting
- Example: marketing and operations can return `STRONG_MATCH` while expected notes say `POSSIBLE_MATCH`.
- Expected behavior: report should preserve this as a calibration signal, not fail execution.
- Acceptance criteria: expected-band mismatches remain visible and are reviewed during fixture expansion.

### P2-001 Empty Risk Lists Need Monitoring

- Stage: candidate scoring
- Affected area: candidate scoring prompt/reporting
- Example: final full report includes `risks_empty` for backend engineer and marketing specialist.
- Expected behavior: high-confidence strong matches may have low risks, but the model should still surface missing validation when relevant.
- Acceptance criteria: future fixture expansion confirms risk lists are non-empty for incomplete profiles.

### P2-002 Eval Runner Progress Output

- Stage: reporting
- Affected area: `run_evals.py`
- Example: real local LM Studio evals can run several minutes with no progress output.
- Expected behavior: terminal output should show current role/stage without exposing raw model outputs.
- Acceptance criteria: long eval runs show progress and still write the same JSON/Markdown reports.

## Phase 4 Recommendation

Proceed to Phase 4 Pilot Readiness. The eval suite now runs end-to-end against real LM Studio with all 42 stage checks passing and no protected-attribute warnings. Carry the remaining issues as pilot hardening items, not blockers.
