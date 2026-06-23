# Evaluation Fixtures

This directory contains synthetic fixtures for evaluation quality calibration. Fixtures are source inputs and human-authored expectations. They are not mock LLM output and must not be used as a product fallback.

## Structure

- `fixtures/roles/`: synthetic role and job description inputs.
- `fixtures/resumes/`: synthetic candidate resume inputs.
- `fixtures/transcripts/`: synthetic interview transcript inputs.
- `fixtures/expected/`: expected signals and review notes.
- `reports/`: selected public-safe generated reports.

All fixtures in this directory are synthetic and safe for public review. Do not add real candidate resumes, raw interview transcripts, production emails, raw tokens, OTPs, secrets, or customer data.

## Run

Validate fixtures without LM Studio:

```bash
uv run python -m app.scripts.run_evals --dry-run-fixtures
```

Run real local-model evals:

```bash
uv run python -m app.scripts.check_lmstudio
uv run python -m app.scripts.run_evals --all
uv run python -m app.scripts.run_evals --role sales_account_executive
uv run python -m app.scripts.run_evals --stage candidate_scoring
```

The runner uses the same production prompt modules, schemas, `LLMJsonService`, LM Studio client, and successful-output cache as product code. If an output is not cached, LM Studio must be reachable. The runner exits non-zero instead of using fake or cloud LLM output.

## Reports

The public tracked report is:

- [reports/final_42_of_42_eval_report.md](reports/final_42_of_42_eval_report.md)
- [reports/final_42_of_42_eval_report.json](reports/final_42_of_42_eval_report.json)

New generated reports are ignored by default. Review any report for synthetic-only data, no secrets, no raw tokens, no OTPs, and no private local paths before publishing.

See [../docs/evaluation.md](../docs/evaluation.md).
