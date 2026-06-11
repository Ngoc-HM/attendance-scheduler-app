"""User management endpoints (F-01, F-03)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_me(current_user: ActiveUser):
    """Current user's own profile (employees see only their own data, §9.5)."""
    return current_user


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, _admin: AdminUser):
    return user_service.list_users(db)


@router.post("", response_model=UserRead, status_code=201)
def create_user(db: DbSession, payload: UserCreate, _admin: AdminUser):
    """F-01/F-03 — admin creates a user and assigns a role."""
    return user_service.create(db, payload)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(db: DbSession, user_id: int, payload: UserUpdate, _admin: AdminUser):
    return user_service.update(db, user_id, payload)
