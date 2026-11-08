"""Shift-change request logic (locked decision #8, spec §3).

Handles create / list / approve / reject for ShiftChangeRequest.
- create: validates requester_id == current user; enforces kind-specific fields.
- decide: idempotent guard; on approval lazily calls schedule_service.apply_shift_change
  if available; if missing or NotImplementedError → still approves + adds warning.
- strict_review flag is derived at call-site from requester.role.is_fixed (not stored).
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.enums import LeaveStatus, SwapKind, UserStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.shift_change_request import ShiftChangeRequest
from app.models.user import User
from app.schemas.shift_change import ShiftChangeCreate
from app.services import role_code_validation

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_locked_or_404(db: Session, req_id: int) -> ShiftChangeRequest:
    """Load the request with a row lock held until the caller commits
    (``FOR UPDATE`` on PostgreSQL; SQLite ignores it)."""
    req = (
        db.query(ShiftChangeRequest)
        .filter(ShiftChangeRequest.id == req_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("swap.not_found"))
    return req


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
    return user


def _validate_counterpart(db: Session, requester: User, counterpart_id: int) -> None:
    """A swap partner must exist, be someone else, be active and work the same
    codes — otherwise the request could only fail later, at approval."""
    if counterpart_id == requester.id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("swap.counterpart_self")
        )
    counterpart = _get_user_or_404(db, counterpart_id)
    if counterpart.status is not UserStatus.active:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("swap.counterpart_inactive")
        )
    # T and F share {AD, X}: they may swap; A, T/F and M may not mix.
    if role_code_validation.requestable_codes(
        counterpart.role
    ) != role_code_validation.requestable_codes(requester.role):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("swap.counterpart_other_role")
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_request(
    db: Session,
    current_user_id: int,
    payload: ShiftChangeCreate,
) -> tuple[ShiftChangeRequest, bool]:
    """Create a shift-change request for the current user's own cell.

    Returns (ShiftChangeRequest, strict_review) where strict_review reflects
    whether the requester has a fixed role (A1–A4).

    Raises 400 if kind-specific required fields are missing; 404 for an
    unknown swap partner and 422 for oneself, an inactive partner or one with
    other codes; 409 ``swap.own_cell_only`` when the requester has no planned
    cell that day; 422 ``swap.cell_locked`` for a code change on a cell that
    is not a regular working/off day (AL, CD, S, A/D, T, B).
    """
    # Validate kind-specific fields.
    if payload.kind is SwapKind.change_code and payload.requested_code is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t("swap.code_required"))
    if payload.kind is SwapKind.swap_with and payload.counterpart_user_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=t("swap.counterpart_required")
        )

    requester = _get_user_or_404(db, current_user_id)
    if payload.requested_code is not None:
        # Employees ask only for their regular working / off codes; leave (AL),
        # comp days (CD), sickness (S) and admin codes (A/D, T, B) are refused.
        role_code_validation.validate_requestable(requester.role, payload.requested_code)

    if payload.kind is SwapKind.swap_with and payload.counterpart_user_id is not None:
        _validate_counterpart(db, requester, payload.counterpart_user_id)

    # The request is about the requester's own planned cell: no cell (no
    # schedule for that month, or not on it) means nothing to change.
    cell = (
        db.query(ShiftAssignment)
        .join(MonthlySchedule, ShiftAssignment.schedule_id == MonthlySchedule.id)
        .filter(
            MonthlySchedule.year == payload.work_date.year,
            MonthlySchedule.month == payload.work_date.month,
            ShiftAssignment.user_id == current_user_id,
            ShiftAssignment.work_date == payload.work_date,
        )
        .one_or_none()
    )
    if cell is None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("swap.own_cell_only"))
    if (
        payload.kind is SwapKind.change_code
        and cell.code not in role_code_validation.requestable_codes(requester.role)
    ):
        # Leave (AL), comp (CD), sickness and admin-assigned days are not the
        # employee's to re-code (B4); approval checks the cell again.
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("swap.cell_locked")
        )

    req = ShiftChangeRequest(
        requester_id=current_user_id,
        work_date=payload.work_date,
        kind=payload.kind,
        requested_code=payload.requested_code,
        counterpart_user_id=payload.counterpart_user_id,
        status=LeaveStatus.pending,
        note=payload.note,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    strict_review = requester.role.is_fixed
    return req, strict_review


def list_for_user(db: Session, user_id: int) -> list[tuple[ShiftChangeRequest, bool]]:
    """Own requests (newest first). Returns list of (request, strict_review)."""
    reqs = (
        db.query(ShiftChangeRequest)
        .filter(ShiftChangeRequest.requester_id == user_id)
        .order_by(ShiftChangeRequest.created_at.desc())
        .all()
    )
    user = db.get(User, user_id)
    strict = user.role.is_fixed if user else False
    return [(r, strict) for r in reqs]


def list_all(db: Session) -> list[tuple[ShiftChangeRequest, bool]]:
    """Admin view — all requests (newest first)."""
    reqs = (
        db.query(ShiftChangeRequest)
        .order_by(ShiftChangeRequest.created_at.desc())
        .all()
    )
    # Bulk-load requesters for strict_review derivation.
    user_ids = {r.requester_id for r in reqs}
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    users_by_id = {u.id: u for u in users}

    result = []
    for r in reqs:
        u = users_by_id.get(r.requester_id)
        strict = u.role.is_fixed if u else False
        result.append((r, strict))
    return result


def decide(
    db: Session,
    req_id: int,
    new_status: LeaveStatus,
    admin_id: int,
) -> tuple[ShiftChangeRequest, bool, list[str]]:
    """Admin approve or reject a shift-change request.

    On approval, lazily attempts to call schedule_service.apply_shift_change.
    If that seam is missing or raises NotImplementedError the request is still
    approved and a warning is added to the response.

    Returns (request, strict_review, warnings).
    """
    # Row lock (PostgreSQL): a second approve waits here until the first one
    # commits, then sees the request decided — a swap is never applied twice.
    # Cells and status are committed together below.
    req = _get_locked_or_404(db, req_id)

    if req.status != LeaveStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("swap.already_decided"))

    warnings: list[str] = []

    if new_status == LeaveStatus.approved:
        # Phase-05 seam: apply the change to the persisted schedule.
        # HTTPException (e.g. no schedule for that month) propagates to the
        # caller — approving a change that cannot be applied is an error.
        try:
            import app.services.schedule_service as svc  # noqa: PLC0415

            apply_fn = getattr(svc, "apply_shift_change", None)
            if apply_fn is None:
                raise NotImplementedError
            warnings.extend(apply_fn(db, req))
        except NotImplementedError:
            warnings.append("schedule application pending")

    req.status = new_status
    req.decided_by_id = admin_id
    req.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(req)

    requester = db.get(User, req.requester_id)
    strict_review = requester.role.is_fixed if requester else False

    return req, strict_review, warnings
