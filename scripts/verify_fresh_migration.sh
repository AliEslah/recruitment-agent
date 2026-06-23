#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${1:-recruitment_migration_check}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"
docker compose up -d postgres
docker compose exec -T postgres dropdb -U recruitment --if-exists "$DB_NAME"
docker compose exec -T postgres createdb -U recruitment "$DB_NAME"
DATABASE_URL="postgresql+asyncpg://recruitment:recruitment@localhost:5432/$DB_NAME" uv run alembic upgrade head
DATABASE_URL="postgresql+asyncpg://recruitment:recruitment@localhost:5432/$DB_NAME" uv run alembic current
docker compose exec -T postgres dropdb -U recruitment "$DB_NAME"
