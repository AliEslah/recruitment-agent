#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

FAILURES=0
DOCKER_OK=0
POSTGRES_OK=0
MAILPIT_OK=0
BACKEND_CONTAINER_PRESENT=0
MIGRATIONS_OK=0
LMSTUDIO_OK=0

pass() {
  printf 'PASS: %s\n' "$1"
}

fail() {
  printf 'FAIL: %s\n' "$1"
  printf 'NEXT: %s\n' "$2"
  FAILURES=$((FAILURES + 1))
}

info() {
  printf 'INFO: %s\n' "$1"
}

run_check() {
  local label="$1"
  local next_action="$2"
  shift 2
  printf '\n== %s ==\n' "$label"
  if "$@"; then
    pass "$label"
    return 0
  fi
  fail "$label" "$next_action"
  return 1
}

container_running() {
  local service="$1"
  local cid
  cid="$(docker compose ps -q "$service" 2>/dev/null || true)"
  if [[ -z "$cid" ]]; then
    return 1
  fi
  [[ "$(docker inspect -f '{{.State.Running}}' "$cid" 2>/dev/null)" == "true" ]]
}

http_ok() {
  local url="$1"
  curl -fsS --max-time 10 "$url" >/dev/null
}

env_present() {
  local name="$1"
  [[ -n "${!name:-}" ]]
}

python_role_templates_available() {
  (cd "$ROOT_DIR" && uv run python - <<'PY'
from app.services.role_templates import load_role_templates

templates = load_role_templates()
required = {
    "sales_account_executive",
    "customer_support_specialist",
    "operations_manager",
    "hr_generalist",
    "marketing_specialist",
    "finance_analyst",
    "backend_engineer",
}
available = {template.template_id for template in templates}
missing = sorted(required - available)
if missing:
    raise SystemExit(f"missing role templates: {', '.join(missing)}")
print(f"role_templates={len(templates)}")
PY
  )
}

printf 'Pilot Readiness Verification\n'
printf 'Root: %s\n' "$ROOT_DIR"
printf 'API base URL: %s\n' "$API_BASE_URL"
printf 'Started: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
printf 'Policy: full LLM evals are intentionally not run; only run_evals --dry-run-fixtures is allowed.\n'

printf '\n== Docker availability ==\n'
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  DOCKER_OK=1
  pass "Docker availability"
else
  fail "Docker availability" "Start Docker Desktop or the Docker daemon, then rerun scripts/verify_pilot_readiness.sh."
fi

if [[ "$DOCKER_OK" -eq 1 ]]; then
  printf '\n== PostgreSQL container status ==\n'
  if container_running postgres; then
    POSTGRES_OK=1
    pass "PostgreSQL container is running"
  else
    fail "PostgreSQL container status" "Run: docker compose up -d postgres"
  fi

  printf '\n== Mailpit container status ==\n'
  if container_running mailpit; then
    MAILPIT_OK=1
    pass "Mailpit container is running"
  else
    fail "Mailpit container status" "Run: docker compose up -d mailpit"
  fi

  printf '\n== Backend container status ==\n'
  backend_cid="$(docker compose ps -q backend 2>/dev/null || true)"
  if [[ -z "$backend_cid" ]]; then
    info "Backend container is not created. This is acceptable before the backend compose step."
    printf 'NEXT: To run it, use: docker compose up -d --build backend\n'
  elif container_running backend; then
    BACKEND_CONTAINER_PRESENT=1
    pass "Backend container is running"
  else
    BACKEND_CONTAINER_PRESENT=1
    fail "Backend container status" "Run: docker compose up -d --build backend, then inspect logs with docker compose logs --tail=120 backend."
  fi
else
  printf '\n== PostgreSQL container status ==\n'
  fail "PostgreSQL container status" "Docker is unavailable. Start Docker, then run: docker compose up -d postgres"
  printf '\n== Mailpit container status ==\n'
  fail "Mailpit container status" "Docker is unavailable. Start Docker, then run: docker compose up -d mailpit"
  printf '\n== Backend container status ==\n'
  fail "Backend container status" "Docker is unavailable. Start Docker, then run: docker compose up -d --build backend"
fi

if run_check "Database migration status" "Start PostgreSQL with docker compose up -d postgres, verify DATABASE_URL, then rerun: uv run alembic upgrade head" \
  bash -c "cd '$ROOT_DIR' && uv run alembic upgrade head"; then
  MIGRATIONS_OK=1
fi

run_check "Backend health /health" "Start the backend with: uv run uvicorn app.main:app --app-dir backend --reload OR docker compose up -d --build backend" \
  http_ok "$API_BASE_URL/health"
run_check "Backend health /health/db" "Start PostgreSQL, apply migrations, start backend, then retry: curl $API_BASE_URL/health/db" \
  http_ok "$API_BASE_URL/health/db"
run_check "Backend health /health/llm" "Start LM Studio, load RECRUITING_LLM_MODEL, set LM_STUDIO_BASE_URL and LM_STUDIO_API_KEY, then retry: curl $API_BASE_URL/health/llm" \
  http_ok "$API_BASE_URL/health/llm"

printf '\n== Required environment variables ==\n'
for var_name in RECRUITING_LLM_MODEL LM_STUDIO_BASE_URL LM_STUDIO_API_KEY; do
  if env_present "$var_name"; then
    pass "$var_name is set"
  else
    fail "$var_name is not set" "Export it before verification, for example: export $var_name=<value>"
  fi
done

if run_check "LM Studio tiny diagnostic" "Open LM Studio, start the local server, load the configured model, then rerun: uv run python -m app.scripts.check_lmstudio" \
  bash -c "cd '$ROOT_DIR' && uv run python -m app.scripts.check_lmstudio"; then
  LMSTUDIO_OK=1
fi

run_check "Eval fixture dry run only" "Fix synthetic eval fixture loading errors, then rerun: uv run python -m app.scripts.run_evals --dry-run-fixtures" \
  bash -c "cd '$ROOT_DIR' && uv run python -m app.scripts.run_evals --dry-run-fixtures"

run_check "Role templates available" "Restore backend/app/fixtures/role_templates.json and app.services.role_templates, then rerun this script." \
  python_role_templates_available

run_check "Dev users can be seeded" "Start PostgreSQL, apply migrations, configure DEV_* users if needed, then rerun: uv run python -m app.scripts.seed_dev_users" \
  bash -c "cd '$ROOT_DIR' && uv run python -m app.scripts.seed_dev_users"
run_check "Pilot data can be seeded" "Start PostgreSQL, apply migrations, then rerun: uv run python -m app.scripts.seed_pilot_data" \
  bash -c "cd '$ROOT_DIR' && uv run python -m app.scripts.seed_pilot_data"

run_check "Frontend typecheck" "Run npm install in frontend if dependencies are missing, then rerun: npm run typecheck" \
  bash -c "cd '$FRONTEND_DIR' && npm run typecheck"
run_check "Frontend lint" "Fix ESLint findings, then rerun: npm run lint" \
  bash -c "cd '$FRONTEND_DIR' && npm run lint"
run_check "Frontend tests" "Fix Vitest failures, then rerun: npm run test" \
  bash -c "cd '$FRONTEND_DIR' && npm run test"
run_check "Frontend build" "Fix Next.js build failures, then rerun: npm run build" \
  bash -c "cd '$FRONTEND_DIR' && npm run build"

printf '\nPilot readiness verification finished with %s failure(s).\n' "$FAILURES"
if [[ "$FAILURES" -eq 0 ]]; then
  printf 'PASS: Automated pilot readiness checks passed. Complete docs/PILOT_MANUAL_VERIFICATION.md before declaring pilot verification passed.\n'
  exit 0
fi

printf 'FAIL: Pilot readiness is not verified. Resolve the failed checks above and rerun this script.\n'
exit 1
