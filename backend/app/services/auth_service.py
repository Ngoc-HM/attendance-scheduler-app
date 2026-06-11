"""Authentication logic (F-02)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.core.security import create_access_token, verify_password
from app.models.enums import UserStatus
from app.models.user import User


def authenticate(db: Session, username: str, password: str) -> User | None:
    """Return the user if credentials are valid and the account is active.

    Steps: look up by username → ``verify_password`` → check ``status == active``.
    Returns ``None`` on any failure (caller maps it to 401).
    """
    user = db.query(User).filter(User.username == username).one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if user.status is not UserStatus.active:
        return None
    return user


def login(db: Session, username: str, password: str) -> str:
    """Authenticate and return a signed JWT (``sub`` = user id).

    Raises 401 when credentials are invalid or the account is not active.
    """
    user = authenticate(db, username, password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.invalid_credentials"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_access_token(subject=user.id)
