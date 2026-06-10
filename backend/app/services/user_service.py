"""User management logic (F-01, F-03)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def register(db: Session, payload: UserCreate) -> User:
    """F-01 — self-registration; create with status ``pending``."""
    raise NotImplementedError  # TODO


def create(db: Session, payload: UserCreate) -> User:
    """F-01/F-03 — admin creates an active user with an assigned role."""
    raise NotImplementedError  # TODO


def approve(db: Session, user_id: int) -> User:
    """F-01 — activate a pending account."""
    raise NotImplementedError  # TODO


def update(db: Session, user_id: int, payload: UserUpdate) -> User:
    raise NotImplementedError  # TODO


def list_users(db: Session) -> list[User]:
    raise NotImplementedError  # TODO
