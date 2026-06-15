"""Shift-change request endpoints (locked decision #8, spec §3)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.models.enums import LeaveStatus
from app.schemas.shift_change import ShiftChangeCreate, ShiftChangeDecision, ShiftChangeRead
from app.services import audit_service, shift_change_service

router = APIRouter()


def _to_read(req, strict_review: bool, warnings: list[str] | None = None) -> ShiftChangeRead:
    """Convert ORM object + derived fields to ShiftChangeRead."""
    return ShiftChangeRead(
        id=req.id,
        requester_id=req.requester_id,
        work_date=req.work_date,
        kind=req.kind,
        requested_code=req.requested_code,
        counterpart_user_id=req.counterpart_user_id,
        status=req.status,
        note=req.note,
        decided_by_id=req.decided_by_id,
        decided_at=req.decided_at,
        strict_review=strict_review,
        warnings=warnings or [],
    )


@router.post("", response_model=ShiftChangeRead, status_code=status.HTTP_201_CREATED)
def create_shift_change(
    db: DbSession,
    payload: ShiftChangeCreate,
    current_user: ActiveUser,
):
    """Request a change on the current user's own scheduled cell."""
    req, strict_review = shift_change_service.create_request(db, current_user.id, payload)
    return _to_read(req, strict_review)


@router.get("", response_model=list[ShiftChangeRead])
def list_shift_changes(
    db: DbSession,
    current_user: ActiveUser,
    all: bool = Query(False, description="Admin: return all users' requests"),
):
    """Own shift-change requests; admin may pass ?all=true to see all."""
    if all:
        from app.models.enums import Role
        if current_user.role is not Role.M:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")
        pairs = shift_change_service.list_all(db)
    else:
        pairs = shift_change_service.list_for_user(db, current_user.id)

    return [_to_read(req, strict) for req, strict in pairs]


@router.post("/{req_id}/decide", response_model=ShiftChangeRead)
def decide_shift_change(
    db: DbSession,
    req_id: int,
    payload: ShiftChangeDecision,
    admin: AdminUser,
):
    """Admin approves or rejects a shift-change request."""
    if payload.status == LeaveStatus.pending:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Decision status must be 'approved' or 'rejected'.",
        )
    req, strict_review, warnings = shift_change_service.decide(
        db, req_id, payload.status, admin.id
    )
    audit_service.record(db, admin.id, f"shift_change.{payload.status.value}",
                         "ShiftChangeRequest", req_id, detail=f"requester={req.requester_id}")
    return _to_read(req, strict_review, warnings)
