"""Account & authentication endpoints (F-01, F-02, F-03)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AdminUser, DbSession
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.services import auth_service, user_service

router = APIRouter()


@router.post("/login", response_model=Token)
def login(db: DbSession, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """F-02 — exchange username/password for a JWT access token."""
    access_token = auth_service.login(db, form_data.username, form_data.password)
    return Token(access_token=access_token)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(db: DbSession, payload: UserCreate):
    """F-01 — self-registration; account stays ``pending`` until admin approval."""
    return user_service.register(db, payload)


@router.post("/users/{user_id}/approve", response_model=UserRead)
def approve_user(db: DbSession, user_id: int, _admin: AdminUser):
    """F-01 — admin approves a pending account (activates it)."""
    return user_service.approve(db, user_id)
