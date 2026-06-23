# Evaluation Fixtures

This directory contains synthetic fixtures for evaluation quality calibration. The fixtures are not mock LLM output and must not be used as a production fallback. They are source inputs and human-authored expectations for running real local LM Studio evaluations.

## Structure

- `fixtures/roles/`: role and job description inputs.
- `fixtures/resumes/<family>/`: synthetic candidate resume fixtures.
- `fixtures/transcripts/<family>/`: synthetic interview transcript fixtures.
- `fixtures/expected/`: human-readable expected signals and validation gaps.
- `reports/`: generated JSON and Markdown eval reports.

All fixtures in this directory are synthetic and intentionally safe for public review. Do not add real candidate resumes, raw interview transcripts, production emails, tokens, OTPs, or customer data to eval fixtures or reports.

## Run

Use `.env` copied from `.env.example`, or export the eval environment explicitly:

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
uv run python -m app.scripts.run_evals --stage candidate_scoring
uv run python -m app.scripts.run_evals --stage interview_evaluation
uv run python -m app.scripts.run_evals --stage final_scorecard
```

The runner uses the same production prompt modules, schemas, `LLMJsonService`, LM Studio client, and successful-output cache. If an output is not cached, LM Studio must be reachable. The runner exits non-zero rather than using fake or cloud LLM output.

## Metrics

Checks cover criteria weights, duplicate criteria, recommendation band consistency, evidence grounding, missing evidence, protected-attribute terms, interview-question coverage, and cross-stage consistency. These checks are report-only in Phase 3.

## Interpreting Reports

Each run writes:

- `reports/<timestamp>_eval_report.json`
- `reports/<timestamp>_eval_report.md`

Use warnings as calibration signals, not as legal conclusions or deterministic grading. Evidence grounding uses token overlap heuristics, so short paraphrases can be marked weak even when humans would accept them.

Reports include runtime and LLM call usage. `cache_hits` are successful prior real LM Studio outputs from `LLMJsonService`; they are not mock outputs. All Phase 3B quality checks are report-only unless the runner has an infrastructure, JSON, or schema failure.

The public repo keeps only selected useful reports:

- `reports/20260623T100907Z_eval_report.*`: Phase 3B baseline full run.
- `reports/20260623T104144Z_eval_report.*`: Phase 3B after-fix full run.
- `reports/20260623T111250Z_eval_report.*`: final Phase 3C-Lite 42/42 full run.

New generated reports are ignored by default. Review them locally, confirm they contain only synthetic data and no secrets, then update `reports/.gitignore` deliberately if a report should be published.
