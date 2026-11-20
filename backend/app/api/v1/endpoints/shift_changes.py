"""Shift-change request endpoints (locked decision #8, spec §3)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.core.i18n import t
from app.models.enums import AttendanceCode, LeaveStatus, SwapKind
from app.models.shift_change_request import ShiftChangeRequest
from app.models.user import User
from app.schemas.common import ApprovalPreview
from app.schemas.shift_change import (
    ShiftChangeCreate,
    ShiftChangeDecision,
    ShiftChangeRead,
    ShiftChangeResponse,
)
from app.services import audit_service, shift_change_service

router = APIRouter()


def _read_one(
    db: Session,
    req: ShiftChangeRequest,
    viewer: User,
    strict_review: bool,
    warnings: list[str] | None = None,
) -> ShiftChangeRead:
    codes = shift_change_service.roster_codes(db, [req], viewer)
    return _to_read(req, strict_review, codes, warnings)


def _read_many(
    db: Session, pairs: list[tuple[ShiftChangeRequest, bool]], viewer: User
) -> list[ShiftChangeRead]:
    codes = shift_change_service.roster_codes(db, [req for req, _ in pairs], viewer)
    return [_to_read(req, strict, codes) for req, strict in pairs]


def _to_read(
    req: ShiftChangeRequest,
    strict_review: bool,
    codes: dict[tuple[int, date], AttendanceCode],
    warnings: list[str] | None = None,
) -> ShiftChangeRead:
    """Convert ORM object + derived fields to ShiftChangeRead. ``codes`` comes
    from ``shift_change_service.roster_codes`` (one query for the whole list)."""
    counterpart_shift = (
        codes.get((req.counterpart_user_id, req.work_date))
        if req.kind is SwapKind.swap_with and req.counterpart_user_id is not None
        else None
    )
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
        created_at=req.created_at,
        counterpart_status=req.counterpart_status,
        requester_shift=codes.get((req.requester_id, req.work_date)),
        counterpart_shift=counterpart_shift,
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
    return _read_one(db, req, current_user, strict_review)


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
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=t("auth.admin_required"))
        pairs = shift_change_service.list_all(db)
    else:
        pairs = shift_change_service.list_for_user(db, current_user.id)

    return _read_many(db, pairs, current_user)


# Declared before the /{req_id}/... routes.
@router.get("/incoming", response_model=list[ShiftChangeRead])
def incoming_shift_changes(db: DbSession, current_user: ActiveUser):
    """Swaps a colleague asked the caller into, still waiting for an answer."""
    pairs = shift_change_service.list_incoming(db, current_user.id)
    return _read_many(db, pairs, current_user)


@router.post("/{req_id}/respond", response_model=ShiftChangeRead)
def respond_to_swap(
    db: DbSession,
    req_id: int,
    payload: ShiftChangeResponse,
    current_user: ActiveUser,
):
    """The swap partner accepts (the admin decides next) or declines."""
    req = shift_change_service.respond(db, req_id, current_user.id, payload.accept)
    audit_service.record(
        db, current_user.id,
        f"shift_change.counterpart_{'accepted' if payload.accept else 'declined'}",
        "ShiftChangeRequest", req_id, detail=f"requester={req.requester_id}",
    )
    return _read_one(db, req, current_user, False)


@router.get("/{req_id}/approval-preview", response_model=ApprovalPreview)
def preview_shift_change_approval(db: DbSession, req_id: int, _admin: AdminUser):
    """Admin: rule breaches approving this request would add. Nothing is saved."""
    return ApprovalPreview(warnings=shift_change_service.preview_approval(db, req_id))


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
            detail=t("request.decision_status_invalid"),
        )
    req, strict_review, warnings = shift_change_service.decide(
        db, req_id, payload.status, admin.id
    )
    audit_service.record(db, admin.id, f"shift_change.{payload.status.value}",
                         "ShiftChangeRequest", req_id, detail=f"requester={req.requester_id}")
    return _read_one(db, req, admin, strict_review, warnings)
