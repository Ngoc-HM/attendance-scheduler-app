#!/usr/bin/env bash
# Start the development PostgreSQL in Docker and bring its schema to the newest
# migration. Used by `make dev` and `make db`.
#
# It acts only when DATABASE_URL (backend/.env) is a PostgreSQL on this machine
# (localhost): a remote database is never started, migrated or touched here.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT/backend"
PY="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "ERROR: backend venv not found at $PY"
  echo "Run 'make install' first (creates backend/.venv and installs deps)."
  exit 1
fi

# Where does the backend's DATABASE_URL point? Prints one word, never the URL
# (it carries the password): local-postgres | sqlite | remote.
kind="$(cd "$BACKEND_DIR" && "$PY" - <<'PYCODE'
from sqlalchemy.engine.url import make_url

from app.core.config import settings
from app.core.script_guard import is_local_database

if make_url(settings.DATABASE_URL).get_backend_name() == "sqlite":
    print("sqlite")
elif is_local_database(settings.DATABASE_URL):
    print("local-postgres")
else:
    print("remote")
PYCODE
)" || { echo "ERROR: could not read DATABASE_URL from backend/.env"; exit 1; }

if [[ "$kind" != "local-postgres" ]]; then
  echo ">> DATABASE_URL in backend/.env is not a PostgreSQL on this machine ($kind):"
  echo "   Docker PostgreSQL and migrations skipped."
  exit 0
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is not running. Start Docker Desktop, then run this again."
  exit 1
fi

echo ">> PostgreSQL in Docker (localhost:5432)..."
docker compose -f "$BACKEND_DIR/docker-compose.yml" up -d --wait db || {
  echo "ERROR: PostgreSQL did not start (docker compose up db)."
  exit 1
}

echo ">> database migrations (alembic upgrade head)..."
( cd "$BACKEND_DIR" && "$PY" -m alembic upgrade head ) || {
  echo "ERROR: migrations failed."
  exit 1
}
