"""User management endpoints (F-01, F-03).

Every admin mutation here is audited (§9.5): create, role/status/password
update and hard delete.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.core.i18n import t
from app.models.audit import AuditLog
from app.schemas.user import UserCreate, UserDirectoryEntry, UserRead, UserUpdate, UserUpdateResult
from app.services import audit_service, user_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_me(current_user: ActiveUser):
    """Current user's own profile (employees see only their own data, §9.5)."""
    return current_user


# Declared before the /{user_id} routes so "directory" is never read as an id.
@router.get("/directory", response_model=list[UserDirectoryEntry])
def user_directory(db: DbSession, _user: ActiveUser):
    """Active users' codes and roles (no names) for any signed-in user."""
    return user_service.list_directory(db)


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
            ("annual_leave_quota", payload.annual_leave_quota),
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
    """F-03 (extension) — admin hard-deletes a user; cascades history.

    The ``user.delete`` audit row is added to the session after the guards pass
    and is committed by ``user_service.delete`` together with the delete, so a
    failure leaves neither the audit row nor a half-deleted user. The audit row
    cannot follow the delete: once an admin's own row is gone, an audit row
    naming them as actor would violate the foreign key, so a self-delete is
    recorded with no actor and detail ``self``.
    """
    user_service.ensure_deletable(db, user_id)
    is_self = user_id == admin.id
    actor_id = None if is_self else admin.id
    detail = "self" if is_self else None
    db.add(
        AuditLog(
            actor_id=actor_id, action="user.delete", entity="User",
            entity_id=user_id, detail=detail,
        )
    )
    try:
        user_service.delete(db, user_id, acting_admin_id=admin.id)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        # Fail loud like audit_service.record: nothing was committed.
        db.rollback()
        logger.exception(
            "User delete with audit failed: actor=%s action=user.delete "
            "entity=User id=%s detail=%s",
            actor_id, user_id, detail,
        )
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail=t("user.delete_failed")
        ) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
