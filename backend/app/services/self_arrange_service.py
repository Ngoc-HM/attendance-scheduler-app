"""Self-arrange batch logic (owner 2026-07-09).

Flow: employee (T/F; A blocked) proposes a batch of own-cell changes on a
PUBLISHED month → validated (ownership, role code domain, rest rules)
→ pending → admin approves once more → re-validated against the CURRENT
schedule and applied. Validation runs at BOTH ends because the schedule may
change between submit and approve.

Rest semantics (owner 2026-11-10 — the 7-day blocks are gone): the batch
must keep the NUMBER of X the person holds in the month (a day off may move,
never be added or removed), and it must not create a
``rolling_seven_min_two_rest`` or ``max_consecutive_working`` violation for
the requester that was not there before. Both are judged with the re-check
functions and the requester's own history, so the server, the solver and the
admin's re-check agree. AL/S/CD are stored as their own codes and are locked
below, so counting X only is exact.
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
from app.scheduler.calendar_utils import month_days
from app.scheduler.role_codes import codes_for
from app.schemas.self_arrange import SelfArrangeChange, SelfArrangeCreate
from app.services import attendance_service, schedule_history, schedule_service
from app.services.schedule_violation_checker import check_consecutive, check_rolling_rest

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
    409 (missing own cell), 422 (bad code / broken rest rule).
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

    _validate_rest(db, requester, own, changes, year, month)
    return schedule, own


def _validate_rest(
    db: Session,
    requester: User,
    own: dict[date, ShiftAssignment],
    changes: list[SelfArrangeChange],
    year: int,
    month: int,
) -> None:
    """Same month X count, and no new 7-day / 5-in-a-row breach (with history)."""
    boundary = schedule_history.build_boundary_states(db, [requester], year, month)
    state = boundary.get(requester.id)
    check_rest_batch(
        requester,
        own,
        changes,
        month_days(year, month),
        carry_streak=state.carry_streak if state else 0,
        previous_working=state.previous_working if state else {},
    )


def _rest_breaches(
    grid: dict[tuple[int, date], AttendanceCode],
    requester: User,
    days: list[date],
    carry_streak: int,
    previous_working: dict[date, bool],
) -> set[tuple[str, date | None]]:
    roles = {requester.id: requester.role}
    found = check_rolling_rest(grid, roles, days, {requester.id: previous_working})
    found += check_consecutive(grid, roles, {requester.id: carry_streak}, days)
    return {(v.rule, v.day) for v in found}


def check_rest_batch(
    requester: User,
    own: dict[date, ShiftAssignment],
    changes: list[SelfArrangeChange],
    days: list[date],
    *,
    carry_streak: int,
    previous_working: dict[date, bool],
) -> None:
    """Pure part of ``_validate_rest``; raises 422 ``breaks_weekly_off``."""
    before = {(requester.id, d): cell.code for d, cell in own.items()}
    after = {**before, **{(requester.id, c.work_date): c.code for c in changes}}

    def x_count(grid: dict[tuple[int, date], AttendanceCode]) -> int:
        return sum(1 for code in grid.values() if code is AttendanceCode.X)

    new_breaches = _rest_breaches(
        after, requester, days, carry_streak, previous_working
    ) - _rest_breaches(before, requester, days, carry_streak, previous_working)
    if x_count(after) != x_count(before) or new_breaches:
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
        # submit; employees must never end up breaking a rest rule.
        schedule, own = _validate(db, requester, req.year, req.month, changes)
        for c in changes:
            cell = own[c.work_date]
            cell.code = c.code
            cell.is_manual_override = True
            # Every edit moves a still-seeded actual (I1; _validate only
            # accepts a published month anyway).
            attendance_service.sync_planned_cell(db, cell.user_id, cell.work_date, c.code)
        # Informational hard-rule recheck for the admin (same as F-09 edits).
        warnings = [
            v.message for v in schedule_service._recheck_violations(db, schedule)
        ]

    req.status = new_status
    req.decided_by_id = admin_id
    req.decided_at = datetime.now(UTC)
    db.commit()
    db.refresh(req)
    return req, warnings
