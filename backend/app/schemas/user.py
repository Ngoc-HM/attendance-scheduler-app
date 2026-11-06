"""User schemas (F-01, F-02, F-03)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import Role, UserStatus
from app.schemas.common import ORMModel


class RegisterRequest(BaseModel):
    """Self-registration (F-01). There is no ``role``: the admin assigns it
    when approving (F-03); a ``role`` sent by the client is ignored."""

    username: str = Field(min_length=3, max_length=64)
    full_name: str = Field(max_length=128)
    password: str = Field(min_length=6, max_length=128)


class UserCreate(RegisterRequest):
    """Admin-created user: the registration fields plus an assigned role
    (F-01, F-03) and, optionally, the annual leave quota (D4; omitted →
    ``ANNUAL_LEAVE_DEFAULT_DAYS``)."""

    role: Role
    annual_leave_quota: int | None = Field(default=None, ge=0, le=365)


class ApproveRequest(BaseModel):
    """Admin approval of a pending account; the admin picks the role (F-03)."""

    role: Role


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    status: UserStatus | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
    # Days of leave per calendar year (owner decision D4).
    annual_leave_quota: int | None = Field(default=None, ge=0, le=365)


class UserRead(ORMModel):
    id: int
    username: str
    code: str
    full_name: str
    role: Role
    status: UserStatus
    carry_comp: int
    carry_streak: int
    annual_leave_quota: int


class UserUpdateResult(BaseModel):
    """PATCH response — carries soft warnings so the UI can surface them.

    Backend still applies the change; warnings describe side-effects the admin
    should know about (e.g. last active fixed-team member would be removed).
    """

    user: UserRead
    warnings: list[str] = Field(default_factory=list)


class UserDirectoryEntry(ORMModel):
    """Code directory any signed-in user may read (GET /users/directory).

    Deliberately carries no name: the client shows people by their
    confidential code (e.g. "A3", "T1").
    """

    id: int
    code: str
    role: Role
