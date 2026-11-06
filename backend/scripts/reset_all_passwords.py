"""Reset every user password to a chosen value.

Run from anywhere, for example:

    python backend/scripts/reset_all_passwords.py
    python backend/scripts/reset_all_passwords.py --password admin123

Refuses (exit code 2) unless ENVIRONMENT=dev; pass ``--allow-non-dev`` to
run against a staging/prod database on purpose.
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

from sqlalchemy.engine.url import make_url  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.user import User  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset all user passwords")
    parser.add_argument(
        "--password",
        default="admin123",
        help="Password to assign to every user (default: admin123)",
    )
    parser.add_argument(
        "--allow-non-dev",
        action="store_true",
        help="Allow running when ENVIRONMENT is not 'dev' (staging/prod database)",
    )
    return parser.parse_args()


def refuse_outside_dev(allow_non_dev: bool) -> bool:
    """True (after printing why) when this must not run against this database.

    Outside ENVIRONMENT=dev the script refuses unless ``--allow-non-dev`` is
    passed, and prints the database host so the operator sees what they hit.
    """
    if settings.ENVIRONMENT == "dev" or allow_non_dev:
        return False
    host = make_url(settings.DATABASE_URL).host or "(none)"
    print(
        f"Refusing to run: ENVIRONMENT={settings.ENVIRONMENT}, database host={host}. "
        "Re-run with --allow-non-dev if this is really intended.",
        file=sys.stderr,
    )
    return True


def main() -> int:
    args = parse_args()
    if refuse_outside_dev(args.allow_non_dev):
        return 2
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            user.hashed_password = get_password_hash(args.password)
        db.commit()
        print(f"Reset passwords for {len(users)} user(s) to: {args.password}")
        return 0
    except Exception as exc:  # pragma: no cover - CLI error handling
        db.rollback()
        print(f"Failed to reset passwords: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
