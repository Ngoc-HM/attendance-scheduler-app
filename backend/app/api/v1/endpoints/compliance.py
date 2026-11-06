"""Compliance endpoints (§9.3 retention, §9.5 data-subject rights).

* ``POST /compliance/retention/purge`` — admin; deletes personnel records older
  than the cutoff (default: ``DATA_RETENTION_MONTHS`` ago). Audited.
* ``GET /compliance/users/{id}/export`` — the person themself or an admin;
  returns every record held about that person as JSON (Art. 15/20). Audited.

Erasure (Art. 17) is the existing admin ``DELETE /users/{id}``, which cascades
the person's history.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ActiveUser, AdminUser, DbSession, ensure_self_or_admin
from app.schemas.compliance import RetentionPurgeRequest, RetentionPurgeResult
from app.services import audit_service, compliance_service

router = APIRouter()


@router.post("/retention/purge", response_model=RetentionPurgeResult)
def retention_purge(db: DbSession, payload: RetentionPurgeRequest, admin: AdminUser):
    """§9.3 — delete records dated before the cutoff (legal floor enforced)."""
    cutoff, deleted = compliance_service.purge_before(db, payload.before)
    audit_service.record(
        db, admin.id, "compliance.retention_purge", "Retention",
        detail=f"before={cutoff} deleted={deleted}",
    )
    return RetentionPurgeResult(cutoff=cutoff, deleted=deleted)


@router.get("/users/{user_id}/export")
def export_user(db: DbSession, user_id: int, current_user: ActiveUser):
    """§9.5 — data-subject access: own data, or any user for an admin."""
    ensure_self_or_admin(current_user, user_id)
    data = compliance_service.export_user_data(db, user_id)
    audit_service.record(
        db, current_user.id, "compliance.user_export", "User", user_id,
        detail="self" if current_user.id == user_id else "admin",
    )
    return data
