"""Authentication logic (F-02)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.core.security import create_access_token, verify_password
from app.models.enums import UserStatus
from app.models.user import User


def find_by_username(db: Session, username: str) -> User | None:
    """The account a typed username means (owner 2026-11-13).

    Staff type their name as they like, so case and surrounding spaces do
    not matter: "joachim" finds "Joachim". The exact spelling wins; without
    it the name must match exactly one account — older data may hold two
    names that differ only by case, and then neither is guessed.
    """
    name = username.strip()
    exact = db.query(User).filter(User.username == name).one_or_none()
    if exact is not None:
        return exact
    matches = (
        db.query(User)
        .filter(func.lower(User.username) == name.lower())
        .limit(2)
        .all()
    )
    return matches[0] if len(matches) == 1 else None


def authenticate(db: Session, username: str, password: str) -> User | None:
    """Return the user if credentials are valid and the account is active.

    Steps: look up by username (``find_by_username``) → ``verify_password``
    → check ``status == active``.
    Returns ``None`` on any failure (caller maps it to 401).
    """
    user = find_by_username(db, username)
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
