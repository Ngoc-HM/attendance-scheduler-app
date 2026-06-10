"""User schemas (F-01, F-02, F-03)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import Role, UserStatus
from app.schemas.common import ORMModel


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    full_name: str = Field(max_length=128)
    role: Role


class UserCreate(UserBase):
    """Admin-created user, or self-registration (F-01)."""

    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    status: UserStatus | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserRead(ORMModel):
    id: int
    username: str
    full_name: str
    role: Role
    status: UserStatus
    annual_leave_balance: int
    carry_comp: int
    carry_streak: int
