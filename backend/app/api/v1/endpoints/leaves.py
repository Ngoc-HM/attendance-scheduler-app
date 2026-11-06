"""Leave registration endpoints (F-05, F-06)."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.models.enums import LeaveStatus
from app.schemas.leave import ConflictEntry, LeaveCreate, LeaveDecision, LeaveRead, LeaveWindowRead
from app.services import audit_service, leave_service

router = APIRouter()


@router.get("", response_model=list[LeaveRead])
def list_leaves(
    db: DbSession,
    current_user: ActiveUser,
    all: bool = Query(False, description="Admin: return all users' requests"),
):
    """Own leave requests; admin may pass ?all=true to see all."""
    if all:
        # Only admins may view all requests.
        from app.models.enums import Role
        if current_user.role is not Role.M:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")
        return leave_service.list_all(db)
    return leave_service.list_for_user(db, current_user.id)


@router.post("", response_model=LeaveRead, status_code=status.HTTP_201_CREATED)
def request_leave(
    db: DbSession,
    payload: LeaveCreate,
    current_user: ActiveUser,
):
    """F-05/F-06 — register leave (monthly < 5 days, or annual >= 5 days)."""
    return leave_service.create_request(db, current_user.id, payload)


@router.get("/pending", response_model=list[LeaveRead])
def pending_leaves(db: DbSession, _admin: AdminUser):
    """Admin queue: pending requests ordered by submission time."""
    return leave_service.list_pending(db)


# Declared before the /{leave_id}/... routes.
@router.get("/window", response_model=LeaveWindowRead)
def leave_window(_user: ActiveUser):
    """Whether monthly registration is open today, and for which month."""
    return leave_service.window_status()


@router.get("/conflicts", response_model=list[ConflictEntry])
def conflicts_for_date(
    db: DbSession,
    _admin: AdminUser,
    target_date: Annotated[date, Query(alias="date", description="YYYY-MM-DD")],
):
    """Admin: ranked list of competing requests on a given date (advisory)."""
    ranked = leave_service.conflicts_for_date(db, target_date)
    result = []
    for i, req in enumerate(ranked, start=1):
        result.append(
            ConflictEntry(
                id=req.id,
                user_id=req.user_id,
                start_date=req.start_date,
                end_date=req.end_date,
                leave_type=req.leave_type,
                status=req.status,
                note=req.note,
                rank=i,
            )
        )
    return result


@router.post("/{leave_id}/decide", response_model=LeaveRead)
def decide_leave(
    db: DbSession,
    leave_id: int,
    payload: LeaveDecision,
    admin: AdminUser,
):
    """Admin approves or rejects a leave request (spec §3, §5.4 #9)."""
    if payload.status == LeaveStatus.pending:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Decision status must be 'approved' or 'rejected'.",
        )
    decided, warnings = leave_service.decide(db, leave_id, payload.status, admin.id)
    audit_service.record(db, admin.id, f"leave.{payload.status.value}", "LeaveRequest",
                         leave_id, detail=f"user={decided.user_id}")
    return LeaveRead.model_validate(decided).model_copy(
        update={"warnings": warnings}
    )


@router.post("/{leave_id}/revoke", response_model=LeaveRead)
def revoke_leave(db: DbSession, leave_id: int, admin: AdminUser):
    """Admin revokes a previously APPROVED leave (owner 2026-07-17).

    Restores the balance and rejects the request; warns when an
    already-generated month still shows the leave until regenerated.
    """
    revoked, warnings = leave_service.revoke(db, leave_id, admin.id)
    audit_service.record(db, admin.id, "leave.revoked", "LeaveRequest",
                         leave_id, detail=f"user={revoked.user_id}")
    return LeaveRead.model_validate(revoked).model_copy(
        update={"warnings": warnings}
    )
