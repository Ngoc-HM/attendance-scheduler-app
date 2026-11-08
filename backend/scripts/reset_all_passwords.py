"""Reset every user password to a chosen value.

Run from anywhere; the new password is required, for example:

    python backend/scripts/reset_all_passwords.py --password 'a-local-test-pw'

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

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.script_guard import refuse_unless_safe  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.user import User  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset all user passwords")
    parser.add_argument(
        "--password",
        required=True,
        help="Password to assign to every user (required; there is no default)",
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
    refused = refuse_unless_safe(settings, args.allow_non_dev)
    if refused is not None:
        return refused
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            user.hashed_password = get_password_hash(args.password)
        db.commit()
        print(f"Reset passwords for {len(users)} user(s).")
        return 0
    except Exception as exc:  # pragma: no cover - CLI error handling
        db.rollback()
        print(f"Failed to reset passwords: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
