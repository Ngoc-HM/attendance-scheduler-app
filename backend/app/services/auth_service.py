"""Authentication logic (F-02)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User


def authenticate(db: Session, username: str, password: str) -> User | None:
    """Return the user if credentials are valid and the account is active.

    Steps: look up by username, ``verify_password`` (see ``core.security``),
    check ``status == active``.
    """
    raise NotImplementedError  # TODO (F-02)


def login(db: Session, username: str, password: str) -> str:
    """Authenticate and return a signed JWT (``core.security.create_access_token``)."""
    raise NotImplementedError  # TODO (F-02)
