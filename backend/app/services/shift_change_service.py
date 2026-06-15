"""Shift-change request logic (locked decision #8, spec §3).

Handles create / list / approve / reject for ShiftChangeRequest.
- create: validates requester_id == current user; enforces kind-specific fields.
- decide: idempotent guard; on approval lazily calls schedule_service.apply_shift_change
  if available; if missing or NotImplementedError → still approves + adds warning.
- strict_review flag is derived at call-site from requester.role.is_fixed (not stored).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.enums import LeaveStatus, SwapKind
from app.models.shift_change_request import ShiftChangeRequest
from app.models.user import User
from app.schemas.shift_change import ShiftChangeCreate


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_404(db: Session, req_id: int) -> ShiftChangeRequest:
    req = db.get(ShiftChangeRequest, req_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("swap.not_found"))
    return req


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
    return user


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

    Raises 400 if kind-specific required fields are missing.
    """
    # Validate kind-specific fields.
    if payload.kind is SwapKind.change_code and payload.requested_code is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t("swap.code_required"))
    if payload.kind is SwapKind.swap_with and payload.counterpart_user_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=t("swap.counterpart_required")
        )

    requester = _get_user_or_404(db, current_user_id)

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
    req = _get_or_404(db, req_id)

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
    req.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)

    requester = db.get(User, req.requester_id)
    strict_review = requester.role.is_fixed if requester else False

    return req, strict_review, warnings
