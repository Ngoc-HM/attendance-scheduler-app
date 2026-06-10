"""User management endpoints (F-01, F-03)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_me(current_user: ActiveUser):
    """Current user's own profile (employees see only their own data, §9.5)."""
    return current_user


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, _admin: AdminUser):
    # TODO: delegate to user_service.list_users(db)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(db: DbSession, payload: UserCreate, _admin: AdminUser):
    """F-01/F-03 — admin creates a user and assigns a role."""
    # TODO: delegate to user_service.create(db, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.patch("/{user_id}", response_model=UserRead)
def update_user(db: DbSession, user_id: int, payload: UserUpdate, _admin: AdminUser):
    # TODO: delegate to user_service.update(db, user_id, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
