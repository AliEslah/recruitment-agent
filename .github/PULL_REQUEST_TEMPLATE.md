## Summary


## Type Of Change

- [ ] Bug fix
- [ ] Documentation
- [ ] Test or eval
- [ ] Refactor
- [ ] Infrastructure

## Verification

- [ ] `uv run pytest -q`
- [ ] `uv run ruff check backend/app tests`
- [ ] `uv run alembic upgrade head`
- [ ] `uv run python -m app.scripts.run_evals --dry-run-fixtures`
- [ ] `cd frontend && npm run typecheck`
- [ ] `cd frontend && npm run lint`
- [ ] `cd frontend && npm run test`
- [ ] `cd frontend && npm run build`
- [ ] Real LM Studio evals run, or not applicable

## LM Studio

- Model:
- Base URL:
- Real eval report path, if quality-related:

## Safety Checklist

- [ ] No real candidate data.
- [ ] No raw interview tokens or OTPs.
- [ ] No secrets, JWTs, `.env` files, or private local paths.
- [ ] No mock LLM output, fake AI output, or cloud fallback.
- [ ] Docs updated for user-facing or operational changes.

