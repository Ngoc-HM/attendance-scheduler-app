"""Self-arrange batch endpoints (owner 2026-07-09).

Employee proposes a batch rearrangement of OWN cells on a published month;
admin approves once more (mirrors the shift-change flow, but batched).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.models.enums import LeaveStatus, Role
from app.schemas.self_arrange import (
    SelfArrangeCreate,
    SelfArrangeDecision,
    SelfArrangeRead,
)
from app.services import audit_service, self_arrange_service

router = APIRouter()


def _to_read(req, warnings: list[str] | None = None) -> SelfArrangeRead:
    return SelfArrangeRead(
        id=req.id,
        requester_id=req.requester_id,
        year=req.year,
        month=req.month,
        changes=req.changes,
        status=req.status,
        note=req.note,
        decided_by_id=req.decided_by_id,
        decided_at=req.decided_at,
        created_at=req.created_at,
        warnings=warnings or [],
    )


@router.post("", response_model=SelfArrangeRead, status_code=status.HTTP_201_CREATED)
def create_self_arrange(
    db: DbSession, payload: SelfArrangeCreate, current_user: ActiveUser
):
    """Propose a batch rearrangement of the current user's own cells."""
    req = self_arrange_service.create(db, current_user, payload)
    audit_service.record(
        db, current_user.id, "self_arrange.create", "SelfArrangeRequest", req.id,
        detail=f"{req.year}-{req.month:02d} x{len(req.changes)}",
    )
    return _to_read(req)


@router.get("", response_model=list[SelfArrangeRead])
def list_self_arrange(
    db: DbSession,
    current_user: ActiveUser,
    all: bool = Query(False, description="Admin: return all users' requests"),
    pending: bool = Query(False, description="With all=true: pending only"),
):
    """Own requests; admin may pass ?all=true (optionally &pending=true)."""
    if all:
        if current_user.role is not Role.M:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only")
        reqs = self_arrange_service.list_all(db, pending_only=pending)
    else:
        reqs = self_arrange_service.list_for_user(db, current_user.id)
    return [_to_read(r) for r in reqs]


@router.post("/{req_id}/decide", response_model=SelfArrangeRead)
def decide_self_arrange(
    db: DbSession, req_id: int, payload: SelfArrangeDecision, admin: AdminUser
):
    """Admin approves (re-validates + applies to the schedule) or rejects."""
    if payload.status == LeaveStatus.pending:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Decision status must be 'approved' or 'rejected'.",
        )
    req, warnings = self_arrange_service.decide(db, req_id, payload.status, admin.id)
    audit_service.record(
        db, admin.id, f"self_arrange.{payload.status.value}",
        "SelfArrangeRequest", req_id, detail=f"requester={req.requester_id}",
    )
    return _to_read(req, warnings)
