# Evaluation Quality Calibration

Phase 3 adds a local evaluation framework for job calibration, resume parsing, candidate scoring, interview planning, interview evaluation, and final scorecards.

## No-Mock Policy

Evaluation fixtures are allowed because they are synthetic source inputs and human-authored expectations. The eval runner never fabricates model outputs, never calls cloud LLM providers, and never falls back when LM Studio is unavailable. Cached outputs are accepted only when they were previously produced by the real LM Studio path through `LLMJsonService`.

## How To Run

Use `.env` copied from `.env.example`, or export the model settings in the shell running evals:

```bash
export RECRUITING_LLM_MODEL=qwen/qwen3-4b-2507
export LM_STUDIO_BASE_URL=http://localhost:1234/v1
export LM_STUDIO_API_KEY=lm-studio
export LM_STUDIO_TEMPERATURE=0.2
export LM_STUDIO_TIMEOUT_SECONDS=180
export LM_STUDIO_MAX_TOKENS=2048
export LM_STUDIO_ENABLE_THINKING=false
export RECRUITING_ALLOW_THINKING_MODEL_FOR_JSON=false
```

```bash
uv run python -m app.scripts.check_lmstudio
uv run python -m app.scripts.run_evals --dry-run-fixtures
uv run python -m app.scripts.run_evals --all
uv run python -m app.scripts.run_evals --role sales_account_executive
uv run python -m app.scripts.run_evals --stage interview_evaluation
uv run python -m app.scripts.run_evals --stage final_scorecard
```

Generated reports are written under `evals/reports/`. The repository intentionally tracks only selected public-safe reports referenced from docs, and ignores new report output by default. Review generated reports for synthetic-only data, local paths, raw tokens, OTPs, and secrets before deciding to publish them.

Required setup:

- PostgreSQL is reachable through `DATABASE_URL`.
- LM Studio local server is running.
- `RECRUITING_LLM_MODEL` names a loaded non-thinking structured-output model.
- `LM_STUDIO_ENABLE_THINKING=false` for JSON workflows.
- Missing `RECRUITING_LLM_MODEL` is a configuration failure. The eval runner must not silently choose a model.

## Fixture Shape

Role fixtures include title, department, seniority, location, employment type, raw JD, expected must-haves, expected nice-to-haves, soft skills, disqualifiers, knockout areas, and scoring notes.

Candidate fixtures include candidate id, synthetic name, resume text, expected strengths, risks, missing evidence, recommendation band, and human notes.

Transcript fixtures include candidate id, job id, chat messages, expected soft-skill notes, red flags, missing evidence, recommendation band, and human notes.

## Checks

The runner reports:

- Job calibration: criteria weight total, duplicate criteria, must-haves, knockout areas, and protected-term warnings.
- Resume parsing: plausible email, numeric years of experience, links present in source, and unsupported parsed claims.
- Candidate scoring: evidence on every criterion, grounding against resume text, risk coverage, recommendation band consistency, and protected-term warnings.
- Interview planning: fixed, resume-validation, soft-skill, knockout, mandatory, duplicate, and protected-term checks.
- Interview evaluation: transcript-grounded evidence, red flags, soft-skill evidence, missing evidence, protected-term warnings, and overclaim risk.
- Final scorecard: required score fields, risk level, evidence summary, missing evidence, human-next-step language, and protected-term warnings.
- Consistency: resume skill validation gaps, new interview-positive signals, resume/interview score divergence, and risks omitted from final scorecards.

## Report-Only Vs Blocking

All new Phase 3 quality checks are report-only. Production flows still persist the model outputs accepted by the existing schemas and business rules. The runner exits non-zero for infrastructure or schema failures, not because a candidate is a weak match.

Pilot readiness is blocked by eval execution failures, schema validation failures, protected-attribute usage in scoring or interview questions, and major unsupported evidence that affects recommendations. Current report-only items include weak evidence overlap, expected-band mismatches, score-band calibration warnings, and resume claims that still need interview validation.

## Limitations

Evidence grounding uses simple token overlap and can miss valid paraphrases. Protected-term scanning is a lightweight guardrail, not a legal compliance engine. Recommendation band checks use coarse score thresholds and should be tuned after several real local-model eval runs.
