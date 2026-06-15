"""User management logic (F-01, F-03)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.core.security import get_password_hash
from app.models.enums import Role, UserStatus
from app.models.role_code_counter import RoleCodeCounter
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def next_user_code(db: Session, role: Role) -> str:
    """Allocate the next never-reused code for a role (e.g. 'A1', 'T2'). Caller commits."""
    counter = (
        db.query(RoleCodeCounter)
        .filter(RoleCodeCounter.role == role.value)
        .with_for_update()
        .one_or_none()
    )
    if counter is None:
        counter = RoleCodeCounter(role=role.value, next_seq=0)
        db.add(counter)
        db.flush()
    counter.next_seq += 1
    return f"{role.value}{counter.next_seq}"


def _get_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
    return user


def _ensure_username_free(db: Session, username: str) -> None:
    exists = db.query(User).filter(User.username == username).one_or_none()
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("user.username_taken"))


def _persist_new(db: Session, payload: UserCreate, status_: UserStatus) -> User:
    _ensure_username_free(db, payload.username)
    user = User(
        username=payload.username,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=get_password_hash(payload.password),
        status=status_,
        code=next_user_code(db, payload.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register(db: Session, payload: UserCreate) -> User:
    """F-01 — self-registration; created ``pending`` until an admin approves."""
    return _persist_new(db, payload, UserStatus.pending)


def create(db: Session, payload: UserCreate) -> User:
    """F-01/F-03 — admin creates an active user with an assigned role."""
    return _persist_new(db, payload, UserStatus.active)


def approve(db: Session, user_id: int) -> User:
    """F-01 — activate a pending account."""
    user = _get_or_404(db, user_id)
    user.status = UserStatus.active
    db.commit()
    db.refresh(user)
    return user


def update(db: Session, user_id: int, payload: UserUpdate) -> User:
    """F-03 — admin edits profile/role/status (and optionally resets password)."""
    user = _get_or_404(db, user_id)
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None and payload.role != user.role:
        user.role = payload.role
        # Reassign a new code that matches the new role letter; old code not reused.
        user.code = next_user_code(db, payload.role)
    elif payload.role is not None:
        user.role = payload.role
    if payload.status is not None:
        user.status = payload.status
    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).all()
