# Phase 3B Quality Issues

## P0

### P0-001 Resume Parsing Null Lists Broke Eval Execution

- Stage: resume parsing
- Affected area: `ParsedResumeOutput`, `parse_resume_prompt`
- Example: real eval run failed when `education`, `certifications`, `projects`, and `links` were returned as `null`.
- Expected behavior: absent list fields should be `[]` or be normalized to empty lists without blocking eval execution.
- Status: fixed in `resume-parsing-v3` and schema list validators.
- Acceptance criteria: `run_evals --all` completes without schema validation errors; helper tests cover null-list normalization.

## P1

### P1-001 Candidate Scoring Still Uses Unsupported Evidence

- Stage: candidate scoring
- Affected area: `candidate-scoring-v4`, evidence grounding helper
- Example from final report: customer support inferred calm empathetic tone from indirect signals; sales inferred handoff/expansion case-study work not present in the resume.
- Expected behavior: every scoring evidence item should quote or tightly summarize resume/profile evidence.
- Acceptance criteria: customer support and sales candidate-scoring stages pass evidence grounding with no unsupported evidence.

### P1-002 Candidate Recommendations Remain Over-Strong

- Stage: candidate scoring
- Affected area: candidate scoring prompt, recommendation-band checks
- Example from final report: operations manager remains `STRONG_MATCH` while fixture expected band is `POSSIBLE_MATCH`.
- Expected behavior: material validation gaps should reduce the recommendation to `POSSIBLE_MATCH` unless evidence is very strong.
- Acceptance criteria: roles with fixture expected `POSSIBLE_MATCH` do not return `STRONG_MATCH` unless the report explicitly justifies the deviation.

### P1-003 Interview Evaluation Has One Remaining Transcript-Grounding Failure

- Stage: interview evaluation
- Affected area: `interview-evaluation-v4`, evidence grounding helper
- Example from final report: customer support evidence summary mixes transcript handling with non-transcript support workflow claims.
- Expected behavior: interview evidence should use transcript answers only; resume-only signals belong in missing evidence or consistency warnings.
- Acceptance criteria: customer support interview evaluation passes evidence grounding without unsupported evidence.

### P1-004 Score-Band Helper Is Too Coarse For Gap-Aware Recommendations

- Stage: candidate scoring
- Affected area: `check_recommendation_band`
- Example from final report: HR and marketing return `POSSIBLE_MATCH` with scores of 88 and 89, which is behaviorally reasonable but flagged by score-only thresholds.
- Expected behavior: recommendation consistency should account for material risks and missing evidence, not score alone.
- Acceptance criteria: helper either uses gap-aware logic or emits a lower-priority calibration note when high score plus `POSSIBLE_MATCH` is justified by risks.

### P1-005 Interview Plan Can Miss Soft-Skill Coverage

- Stage: interview planning
- Affected area: `interview-planning-v2`
- Example from final report: backend engineer plan missed the `SOFT_SKILL` question type.
- Expected behavior: every interview plan should include fixed, resume-validation, soft-skill, and knockout question types.
- Acceptance criteria: all role interview plans include at least one explicit `SOFT_SKILL` question.

## P2

### P2-001 Eval Runner Needs Progress Output

- Stage: reporting
- Affected area: `run_evals.py`
- Example from real run: full uncached evals took several minutes with no terminal progress until report write.
- Expected behavior: runner should print role/stage progress without exposing raw model outputs.
- Acceptance criteria: long eval runs show current role and stage in stdout while preserving JSON/Markdown report outputs.

### P2-002 Expand Fixtures For More Calibration Contrast

- Stage: fixtures
- Affected area: `evals/fixtures`
- Example from final report: most candidates have strong resumes, making over-strong recommendation calibration harder to tune.
- Expected behavior: fixture set should include clear weak, borderline, and needs-review candidates per family.
- Acceptance criteria: each major family has at least one strong, one possible, and one weak/needs-review candidate fixture.

### P2-003 Improve Report Readability Around Recommendation Text

- Stage: reporting
- Affected area: Markdown report rendering
- Example from reports: final/interview recommendations are free text and can clutter distribution summaries.
- Expected behavior: reports should separate candidate band distributions from free-text next-step recommendations.
- Acceptance criteria: Markdown report shows band counts separately from narrative recommendation examples.

### P2-004 Keep No-Mock Policy Visible In Eval Docs

- Stage: documentation
- Affected area: `README.md`, `evals/README.md`, `docs/EVALUATION_QUALITY_PLAN.md`
- Example: users must export the model env var or provide `.env`; no fallback should be implied.
- Expected behavior: docs show exact env setup and state that missing LM Studio config fails the run.
- Acceptance criteria: a new developer can run `check_lmstudio` and `run_evals --all` with the documented env block.
