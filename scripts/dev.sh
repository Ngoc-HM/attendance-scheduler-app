#!/usr/bin/env bash
# Run the FastAPI backend and the Flutter desktop client together.
# The backend runs in the background; Flutter runs in the foreground. Quitting
# Flutter (or Ctrl-C) stops the backend too. Only the backend PID is killed —
# never the parent `make`/shell (that was the `kill 0` footgun).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEVICE="${1:-macos}"
PORT="${2:-8035}"
BACKEND_DIR="$ROOT/backend"
FLUTTER_DIR="$ROOT/attendance_scheduler_app"
PY="$BACKEND_DIR/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "ERROR: backend venv not found at $PY"
  echo "Run 'make install' first (creates backend/.venv and installs deps)."
  exit 1
fi

echo ">> backend :$PORT + Flutter desktop ($DEVICE) — quit Flutter or press Ctrl-C to stop both"

# Start the backend in the background (exec so BACKEND_PID is the uvicorn PID).
( cd "$BACKEND_DIR" && exec "$PY" -m uvicorn app.main:app --reload --port "$PORT" ) &
BACKEND_PID=$!

cleanup() {
  trap - EXIT INT TERM
  echo
  echo ">> stopping backend (pid $BACKEND_PID)..."
  kill "$BACKEND_PID" 2>/dev/null
  wait "$BACKEND_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

# Foreground: Flutter desktop. When it exits, the trap stops the backend.
( cd "$FLUTTER_DIR" && flutter run -d "$DEVICE" )
