"""User management endpoints (F-01, F-03).

Every admin mutation here is audited (§9.5): create, role/status/password
update and hard delete.
"""
from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserUpdateResult
from app.services import audit_service, user_service

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_me(current_user: ActiveUser):
    """Current user's own profile (employees see only their own data, §9.5)."""
    return current_user


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, _admin: AdminUser):
    return user_service.list_users(db)


@router.post("", response_model=UserRead, status_code=201)
def create_user(db: DbSession, payload: UserCreate, admin: AdminUser):
    """F-01/F-03 — admin creates a user and assigns a role."""
    user = user_service.create(db, payload)
    audit_service.record(
        db, admin.id, "user.create", "User", user.id,
        detail=f"username={user.username} role={user.role.value}",
    )
    return user


@router.patch("/{user_id}", response_model=UserUpdateResult)
def update_user(
    db: DbSession, user_id: int, payload: UserUpdate, admin: AdminUser
):
    user, warnings = user_service.update(db, user_id, payload)
    changed = [
        name
        for name, value in (
            ("full_name", payload.full_name),
            ("role", payload.role),
            ("status", payload.status),
            ("password", payload.password),
        )
        if value is not None
    ]
    # Never log the password itself — only that it was changed.
    audit_service.record(
        db, admin.id, "user.update", "User", user.id,
        detail=f"fields={','.join(changed) or 'none'} role={user.role.value} "
               f"status={user.status.value}",
    )
    return UserUpdateResult(user=UserRead.model_validate(user), warnings=warnings)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(db: DbSession, user_id: int, admin: AdminUser) -> Response:
    """F-03 (extension) — admin hard-deletes a user; cascades history."""
    user_service.delete(db, user_id)
    audit_service.record(db, admin.id, "user.delete", "User", user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
