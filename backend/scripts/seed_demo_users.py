"""CLI tool to seed 10 deterministic demo users.

Run from anywhere; ``backend/.env`` is loaded by its absolute path. The demo
password is read with a hidden prompt (asked twice), for example:

    python backend/scripts/seed_demo_users.py

``--password`` keeps working for non-interactive use, but leaves the password
in the shell history and the process list.

Refuses (exit code 2) unless ENVIRONMENT=dev AND the database is local
(SQLite, localhost, 127.0.0.1 or ::1); pass ``--allow-non-dev`` to run
against any other database on purpose (see ``app.core.script_guard``).
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = BACKEND_ROOT / ".venv" / "bin" / "python"
if (
    importlib.util.find_spec("sqlalchemy") is None
    and VENV_PYTHON.exists()
    and sys.executable != str(VENV_PYTHON)
):
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), __file__, *sys.argv[1:]])

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Before the settings import: the settings read '.env' relative to the cwd.
from app.core import script_guard  # noqa: E402

script_guard.load_backend_env(BACKEND_ROOT / ".env")

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.services.demo_user_seed import DEMO_USERS, seed_demo_users  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed 10 demo users")
    parser.add_argument(
        "--password",
        default=None,
        help=(
            "Password to assign to every seeded user (non-interactive use; omit "
            "it to be prompted without echo)"
        ),
    )
    parser.add_argument(
        "--allow-non-dev",
        action="store_true",
        help=(
            "Allow running when ENVIRONMENT is not 'dev' or the database is not "
            "local (shared/remote/staging/prod database)"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    refused = script_guard.refuse_unless_safe(settings, args.allow_non_dev)
    if refused is not None:
        return refused
    password = script_guard.read_password(args.password)
    if password is None:
        return 1
    db = SessionLocal()
    try:
        result = seed_demo_users(db, password)
    finally:
        db.close()

    print(
        f"Seeded demo users: created={result['created']} "
        f"skipped={result['skipped']} total={result['total']}"
    )
    for spec in DEMO_USERS:
        print(f"- {spec.username} ({spec.role.value})")
    if result["skipped"]:
        print("Existing users kept their current password.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
