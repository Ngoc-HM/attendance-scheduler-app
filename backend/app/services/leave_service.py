"""Leave logic (F-05, F-06) and conflict-priority helpers (§5.4 #9).

Implements:
- create_request: window validation, classification, overlap guard, persist.
- list_for_user / list_all / list_pending: query helpers.
- decide: approve/reject with annual_leave_balance decrement/restore.
- approved_off_map: scheduler input — approved requests → {user_id: {date: AL}}.
- conflicts_for_date: returns ranked competing requests for a given date.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.enums import AttendanceCode, LeaveStatus, LeaveType
from app.models.leave import LeaveRequest
from app.models.user import User
from app.schemas.leave import LeaveCreate
from app.services import leave_conflict_resolver
from app.services.leave_windows import classify, is_annual_window_open, is_monthly_window_open


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_404(db: Session, leave_id: int) -> LeaveRequest:
    req = db.get(LeaveRequest, leave_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("leave.not_found"))
    return req


def _has_overlap(db: Session, user_id: int, start: date, end: date, exclude_id: int | None = None) -> bool:
    """Return True if any pending/approved request for user overlaps [start, end]."""
    q = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status.in_([LeaveStatus.pending, LeaveStatus.approved]),
            LeaveRequest.start_date <= end,
            LeaveRequest.end_date >= start,
        )
    )
    if exclude_id is not None:
        q = q.filter(LeaveRequest.id != exclude_id)
    return q.first() is not None


def _day_count(start: date, end: date) -> int:
    """Inclusive calendar-day count between start and end."""
    return (end - start).days + 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_request(db: Session, user_id: int, payload: LeaveCreate, today: date | None = None) -> LeaveRequest:
    """F-05/F-06 — validate window, classify, check overlap, persist pending.

    Parameters
    ----------
    today:
        Injection point for tests; defaults to date.today().
    """
    if today is None:
        today = date.today()

    start = payload.start_date
    end = payload.end_date

    # 1. Basic range check.
    if end < start:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t("leave.invalid_range"))

    # 2. Auto-classify (ignore caller-supplied leave_type per spec).
    leave_type = classify(start, end)

    # 3. Window enforcement.
    if leave_type is LeaveType.monthly:
        if not is_monthly_window_open(today, start.month, start.year):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t("leave.window_closed_monthly"))
    else:
        # Annual: submission must be in the calendar year before the leave's start year.
        if not is_annual_window_open(today, start.year):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t("leave.window_closed_annual"))

    # 4. Overlap guard (pending or approved requests for same user).
    if _has_overlap(db, user_id, start, end):
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("leave.overlap"))

    # 5. Persist.
    req = LeaveRequest(
        user_id=user_id,
        start_date=start,
        end_date=end,
        leave_type=leave_type,
        status=LeaveStatus.pending,
        note=payload.note,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def list_for_user(db: Session, user_id: int) -> list[LeaveRequest]:
    """Return all leave requests for a single user, newest first."""
    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.user_id == user_id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )


def list_all(db: Session) -> list[LeaveRequest]:
    """Admin view — all requests, newest first."""
    return db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()


def list_pending(db: Session) -> list[LeaveRequest]:
    """Admin queue — only pending requests."""
    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.status == LeaveStatus.pending)
        .order_by(LeaveRequest.created_at)
        .all()
    )


def decide(db: Session, leave_id: int, new_status: LeaveStatus, admin_id: int) -> LeaveRequest:
    """Admin approve or reject a leave request.

    On approval: decrement user.annual_leave_balance by the day count.
    On rejection of a previously approved request: restore the balance.
    Idempotent re-decision → 409.
    """
    req = _get_or_404(db, leave_id)

    if req.status != LeaveStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("leave.already_decided"))

    if new_status == LeaveStatus.approved:
        user = db.get(User, req.user_id)
        if user is not None:
            days = _day_count(req.start_date, req.end_date)
            if user.annual_leave_balance < days:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, detail=t("leave.balance_insufficient")
                )
            user.annual_leave_balance -= days

    req.status = new_status
    db.commit()
    db.refresh(req)
    return req


def revoke_balance_on_reject(db: Session, req: LeaveRequest) -> None:
    """Restore annual_leave_balance when an approved request is later rejected.

    Called internally; not exposed as an endpoint — admin decides via decide().
    """
    if req.leave_type is LeaveType.annual:
        user = db.get(User, req.user_id)
        if user is not None:
            user.annual_leave_balance += _day_count(req.start_date, req.end_date)
            db.commit()


def approved_off_map(
    db: Session, year: int, month: int
) -> dict[int, dict[date, AttendanceCode]]:
    """Scheduler input: approved requests whose days intersect the given month.

    Returns {user_id: {date: AttendanceCode.AL}} for every approved leave day
    that falls within (year, month).  CD cells are admin-recorded elsewhere
    and are NOT generated here.
    """
    from calendar import monthrange

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    approved = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.status == LeaveStatus.approved,
            LeaveRequest.start_date <= last_day,
            LeaveRequest.end_date >= first_day,
        )
        .all()
    )

    result: dict[int, dict[date, AttendanceCode]] = {}
    for req in approved:
        # Clamp to the requested month.
        effective_start = max(req.start_date, first_day)
        effective_end = min(req.end_date, last_day)
        current = effective_start
        while current <= effective_end:
            result.setdefault(req.user_id, {})[current] = AttendanceCode.AL
            from datetime import timedelta
            current = date(current.year, current.month, current.day) + timedelta(days=1)

    return result


def annual_off_dates(db: Session, year: int, month: int) -> dict[int, set[date]]:
    """Approved ANNUAL-leave days intersecting (year, month), per user.

    These are the sanctioned long breaks (registered the prior year) — the
    scheduler exempts them from the "no more than 5 consecutive OFF days" rule
    (customer clarification 2026-06-12), since >5 consecutive off IS annual
    leave. Monthly leave / CD / weekly X are NOT exempt.
    """
    from calendar import monthrange
    from datetime import timedelta

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    approved = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.status == LeaveStatus.approved,
            LeaveRequest.leave_type == LeaveType.annual,
            LeaveRequest.start_date <= last_day,
            LeaveRequest.end_date >= first_day,
        )
        .all()
    )

    result: dict[int, set[date]] = {}
    for req in approved:
        current = max(req.start_date, first_day)
        end = min(req.end_date, last_day)
        while current <= end:
            result.setdefault(req.user_id, set()).add(current)
            current += timedelta(days=1)
    return result


def conflicts_for_date(
    db: Session, target_date: date
) -> list[LeaveRequest]:
    """Return ranked competing requests (pending + approved) for a given date.

    Uses leave_conflict_resolver.rank with carry_comp look-up.
    """
    requests = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.status.in_([LeaveStatus.pending, LeaveStatus.approved]),
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date,
        )
        .all()
    )
    if not requests:
        return []

    user_ids = {r.user_id for r in requests}
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    users_by_id = {u.id: u for u in users}

    return leave_conflict_resolver.rank(requests, users_by_id)
