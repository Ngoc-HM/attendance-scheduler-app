"""Account & authentication endpoints (F-01, F-02, F-03).

Routes are scaffolded with their final signatures; business logic lives in
``app.services.auth_service`` / ``user_service`` and is wired in as it is
implemented.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AdminUser, DbSession
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.post("/login", response_model=Token)
def login(db: DbSession, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """F-02 — exchange username/password for a JWT access token."""
    # TODO: delegate to auth_service.authenticate(db, form_data.username, form_data.password)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(db: DbSession, payload: UserCreate):
    """F-01 — self-registration; account stays ``pending`` until admin approval."""
    # TODO: delegate to user_service.register(db, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("/users/{user_id}/approve", response_model=UserRead)
def approve_user(db: DbSession, user_id: int, _admin: AdminUser):
    """F-01 — admin approves a pending account (activates it)."""
    # TODO: delegate to user_service.approve(db, user_id)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
