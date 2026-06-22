# Recruitment Agent

Agentic recruitment backend scaffolded for FastAPI, Postgres, uv, LangChain, and LangGraph.

## Local Development

```bash
uv sync --dev
uv run uvicorn recruitment_agent.main:app --reload
uv run pytest
```

## Infrastructure

Create local environment settings from the template:

```bash
cp .env.example .env
```

Run Postgres only:

```bash
docker compose up postgres
```

Run the API in Docker with Postgres:

```bash
docker compose up --build api
```

Run migrations after Postgres is healthy:

```bash
uv run alembic upgrade head
```

Run tests without requiring Postgres:

```bash
uv run pytest
```

## Architecture

- `src/recruitment_agent/main.py` exposes the FastAPI application.
- `src/recruitment_agent/api/` owns HTTP routes and dependencies.
- `src/recruitment_agent/db/` owns SQLAlchemy async session wiring and database models.
- `src/recruitment_agent/agents/` owns LangGraph state, graph construction, nodes, tools, prompts, and orchestration.
- `src/recruitment_agent/services/` provides use-case boundaries between API routes and agent/database internals.
- `src/recruitment_agent/domains/` keeps recruitment-specific concepts isolated by domain.
