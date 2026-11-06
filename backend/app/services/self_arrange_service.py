"""Self-arrange batch logic (owner 2026-07-09).

Flow: employee (T/F; A blocked) proposes a batch of own-cell changes on a
PUBLISHED month → validated (ownership, role code domain, weekly-2-off quota)
→ pending → admin approves once more → re-validated against the CURRENT
schedule and applied. Validation runs at BOTH ends because the schedule may
change between submit and approve.

Quota semantics (owner decision c): every 7-day block (anchored at day 1)
must keep EXACTLY ``partial_block_off_target`` genuine X days. AL/S/CD are
stored as their own codes in the grid, so counting X only matches decision #4
("leave does not consume the weekly off quota").
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.enums import AttendanceCode, LeaveStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.self_arrange_request import SelfArrangeRequest
from app.models.user import User
from app.scheduler.calendar_utils import (
    build_weeks,
    month_days,
    partial_block_off_target,
)
from app.scheduler.role_codes import codes_for
from app.schemas.self_arrange import SelfArrangeChange, SelfArrangeCreate
from app.services import schedule_service

# ---------------------------------------------------------------------------
# Validation core (shared by create and approve)
# ---------------------------------------------------------------------------

def _validate(
    db: Session,
    requester: User,
    year: int,
    month: int,
    changes: list[SelfArrangeChange],
) -> tuple[MonthlySchedule, dict[date, ShiftAssignment]]:
    """Validate a proposed batch; return (schedule, own cells by date).

    Raises 403 (fixed role), 404 (month not published), 400 (empty/duplicate),
    409 (missing own cell), 422 (bad code / broken weekly-off quota).
    """
    if requester.role.is_fixed:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail=t("selfarrange.forbidden_role")
        )
    if not changes:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=t("selfarrange.empty_changes")
        )
    dates = [c.work_date for c in changes]
    if len(set(dates)) != len(dates):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=t("selfarrange.empty_changes")
        )

    # Published months only — schedule_service.get raises 404 on drafts/absent.
    schedule = schedule_service.get(db, year, month, include_draft=False)

    own = {
        a.work_date: a
        for a in schedule.assignments
        if a.user_id == requester.id
    }
    # CD is in every role's solver domain (holiday work earns it), but it is
    # granted only against comp debt — never something the employee picks or
    # rearranges. Leaving it out also keeps an owed CD cell locked below.
    allowed = set(codes_for(requester.role)) - {AttendanceCode.CD}
    for c in changes:
        if (c.work_date.year, c.work_date.month) != (year, month):
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail=t("selfarrange.cell_not_found")
            )
        if c.work_date not in own:
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail=t("selfarrange.cell_not_found")
            )
        if c.code not in allowed:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=t("selfarrange.invalid_code"),
            )
        # The TARGET cell must itself hold a flexible code: approved leave /
        # sick days (AL, S, CD…) are pinned by the leave lifecycle and must
        # never be rearranged away by the employee (review finding H1).
        if own[c.work_date].code not in allowed:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=t("selfarrange.cell_locked"),
            )

    _validate_weekly_off(own, changes, year, month)
    return schedule, own


def _validate_weekly_off(
    own: dict[date, ShiftAssignment],
    changes: list[SelfArrangeChange],
    year: int,
    month: int,
) -> None:
    """Every AFFECTED 7-day block must keep exactly its X target after the batch."""
    new_codes = {c.work_date: c.code for c in changes}
    changed_dates = set(new_codes)
    for block in build_weeks(month_days(year, month)):
        if not changed_dates.intersection(block):
            continue
        target = partial_block_off_target(len(block))
        got = 0
        for d in block:
            code = new_codes.get(d)
            if code is None:
                cell = own.get(d)
                code = cell.code if cell is not None else None
            if code is AttendanceCode.X:
                got += 1
        if got != target:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=t("selfarrange.breaks_weekly_off"),
            )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create(
    db: Session, requester: User, payload: SelfArrangeCreate
) -> SelfArrangeRequest:
    """Validate and persist a pending batch for the requester's own cells."""
    _validate(db, requester, payload.year, payload.month, payload.changes)

    req = SelfArrangeRequest(
        requester_id=requester.id,
        year=payload.year,
        month=payload.month,
        changes=[
            {"work_date": c.work_date.isoformat(), "code": c.code.value}
            for c in payload.changes
        ],
        status=LeaveStatus.pending,
        note=payload.note,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def list_for_user(db: Session, user_id: int) -> list[SelfArrangeRequest]:
    return (
        db.query(SelfArrangeRequest)
        .filter(SelfArrangeRequest.requester_id == user_id)
        .order_by(SelfArrangeRequest.created_at.desc())
        .all()
    )


def list_all(db: Session, pending_only: bool = False) -> list[SelfArrangeRequest]:
    q = db.query(SelfArrangeRequest)
    if pending_only:
        q = q.filter(SelfArrangeRequest.status == LeaveStatus.pending)
    return q.order_by(SelfArrangeRequest.created_at.desc()).all()


def decide(
    db: Session, req_id: int, new_status: LeaveStatus, admin_id: int
) -> tuple[SelfArrangeRequest, list[str]]:
    """Admin approve/reject. Approval re-validates then applies every cell."""
    # Row lock (no-op on SQLite) so concurrent approve/reject cannot both pass
    # the pending guard and double-apply (review finding M3).
    req = db.get(SelfArrangeRequest, req_id, with_for_update=True)
    if req is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=t("selfarrange.not_found")
        )
    if req.status != LeaveStatus.pending:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("selfarrange.already_decided")
        )

    warnings: list[str] = []
    if new_status == LeaveStatus.approved:
        requester = db.get(User, req.requester_id)
        if requester is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
        changes = [
            SelfArrangeChange(work_date=c["work_date"], code=c["code"])
            for c in req.changes
        ]
        # Re-validate against the CURRENT schedule — it may have changed since
        # submit; employees must never end up violating the weekly quota.
        schedule, own = _validate(db, requester, req.year, req.month, changes)
        for c in changes:
            cell = own[c.work_date]
            cell.code = c.code
            cell.is_manual_override = True
        # Informational hard-rule recheck for the admin (same as F-09 edits).
        warnings = [
            f"{v.rule}: {v.message}"
            for v in schedule_service._recheck_violations(db, schedule)
        ]

    req.status = new_status
    req.decided_by_id = admin_id
    req.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(req)
    return req, warnings
