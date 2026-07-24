"""Reset every user password to a chosen value.

Run from anywhere, for example:

    python backend/scripts/reset_all_passwords.py
    python backend/scripts/reset_all_passwords.py --password admin123
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
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
