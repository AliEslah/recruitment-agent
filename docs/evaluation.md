# Evaluation

Evaluation fixtures live under `evals/`. They are synthetic source inputs and human-authored expectations for checking local model behavior. They are not mock LLM output and must not be used as a runtime fallback.

## Fixture Layout

- `evals/fixtures/roles/`: synthetic role and job description inputs.
- `evals/fixtures/resumes/`: synthetic candidate resume inputs.
- `evals/fixtures/transcripts/`: synthetic interview transcript inputs.
- `evals/fixtures/expected/`: human-authored expected signals and review notes.
- `evals/reports/`: selected public-safe generated reports.

## Dry Run

Validate fixture shape without LM Studio:

```bash
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

## Real Local Evals

Start LM Studio with the configured model, then run:

```bash
uv run python -m app.scripts.check_lmstudio
uv run python -m app.scripts.run_evals --all
```

Targeted runs are available:

```bash
uv run python -m app.scripts.run_evals --role sales_account_executive
uv run python -m app.scripts.run_evals --stage candidate_scoring
uv run python -m app.scripts.run_evals --stage interview_evaluation
uv run python -m app.scripts.run_evals --stage final_scorecard
```

The runner uses production prompt modules, schemas, `LLMJsonService`, LM Studio client behavior, and the successful-output cache. If an output is not cached, LM Studio must be reachable. The runner exits non-zero instead of using fake or cloud LLM output.

## Public Report Policy

Generated reports are ignored by default. Review a report before publishing it and confirm it contains only synthetic data, no raw tokens, no OTPs, no secrets, and no private local paths.

The public repo keeps the final synthetic 42-of-42 report:

- [final_42_of_42_eval_report.md](../evals/reports/final_42_of_42_eval_report.md)
- [final_42_of_42_eval_report.json](../evals/reports/final_42_of_42_eval_report.json)

Older timestamped reports were removed from the public tracked set to reduce release noise.

## Metrics

Checks cover criteria weights, duplicate criteria, recommendation band consistency, evidence grounding, missing evidence, protected-attribute terms, interview-question coverage, and cross-stage consistency.

Warnings are calibration signals, not legal conclusions or deterministic grading. Evidence grounding uses token overlap and can miss valid paraphrases. Protected-term scanning is a lightweight guardrail, not a compliance certification.
