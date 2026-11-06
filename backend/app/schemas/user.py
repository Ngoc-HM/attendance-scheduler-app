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
    """Admin-created user with an assigned role (F-01, F-03)."""

    password: str = Field(min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    """Self-registration (F-01). There is no ``role``: the admin assigns it
    when approving (F-03); a ``role`` sent by the client is ignored."""

    username: str = Field(min_length=3, max_length=64)
    full_name: str = Field(max_length=128)
    password: str = Field(min_length=6, max_length=128)


class ApproveRequest(BaseModel):
    """Admin approval of a pending account; the admin picks the role (F-03)."""

    role: Role


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    status: UserStatus | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserRead(ORMModel):
    id: int
    username: str
    code: str
    full_name: str
    role: Role
    status: UserStatus
    carry_comp: int
    carry_streak: int


class UserUpdateResult(BaseModel):
    """PATCH response — carries soft warnings so the UI can surface them.

    Backend still applies the change; warnings describe side-effects the admin
    should know about (e.g. last active fixed-team member would be removed).
    """

    user: UserRead
    warnings: list[str] = Field(default_factory=list)
