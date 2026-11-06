"""Leave logic (F-05, F-06) and conflict-priority helpers (§5.4 #9).

Implements:
- create_request: window validation, classification, overlap guard, persist.
- list_for_user / list_all / list_pending: query helpers.
- decide / revoke: approve, reject or revoke (no quota; advisory warnings only).
- approved_off_map: scheduler input — approved requests → {user_id: {date: AL}}.
- conflicts_for_date: returns ranked competing requests for a given date.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.business_time import business_today
from app.core.config import settings
from app.core.i18n import t
from app.models.enums import AttendanceCode, LeaveStatus, LeaveType, UserStatus
from app.models.leave import LeaveRequest
from app.models.user import User
from app.schemas.leave import LeaveCreate
from app.services import leave_conflict_resolver, schedule_history
from app.services.leave_windows import (
    classify,
    is_annual_window_open,
    is_monthly_window_open,
    registration_last_day,
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_404(db: Session, leave_id: int) -> LeaveRequest:
    req = db.get(LeaveRequest, leave_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("leave.not_found"))
    return req


def _has_overlap(
    db: Session,
    user_id: int,
    start: date,
    end: date,
    exclude_id: int | None = None,
) -> bool:
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_request(
    db: Session,
    user_id: int,
    payload: LeaveCreate,
    today: date | None = None,
    *,
    enforce_window: bool | None = None,
) -> LeaveRequest:
    """F-05/F-06 — validate window, classify, check overlap, persist pending.

    Parameters
    ----------
    today:
        Injection point for tests; defaults to the business date in
        ``settings.TIMEZONE`` (the same clock the autorun uses).
    """
    if today is None:
        today = business_today()
    if enforce_window is None:
        # Development must allow rapid end-to-end testing without waiting for a
        # calendar window. Staging/production keep the business cutoff.
        enforce_window = settings.ENVIRONMENT != "dev"

    start = payload.start_date
    end = payload.end_date

    # 1. Basic range check.
    if end < start:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t("leave.invalid_range"))

    # 2. The span decides the bucket (> 5 consecutive days is annual). A
    # caller-supplied leave_type (two distinct UI flows) must agree with it,
    # otherwise a long leave labelled monthly would dodge the annual rule.
    leave_type = classify(start, end)
    if payload.leave_type is not None and payload.leave_type is not leave_type:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=t("leave.type_span_mismatch"),
        )

    # 3. Window enforcement.
    if enforce_window:
        if leave_type is LeaveType.monthly:
            if not is_monthly_window_open(today, start.month, start.year):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=t("leave.window_closed_monthly").format(
                        day=registration_last_day()
                    ),
                )
        else:
            # Annual: submission must be in the calendar year before the leave's start year.
            if not is_annual_window_open(today, start.year):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=t("leave.window_closed_annual"),
                )

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


def decide(
    db: Session, leave_id: int, new_status: LeaveStatus, admin_id: int
) -> tuple[LeaveRequest, list[str]]:
    """Admin approve or reject a leave request.

    There is NO leave quota/balance (owner 2026-07-18): the only registration
    rule is the timing window (≤5 days = monthly window; >5 days must be filed
    the previous year). Approving simply flips the status. Idempotent
    re-decision → 409.

    Returns (request, warnings): warnings surface an already-generated month
    (stale schedule) and any flight-coverage impact — advisory only, the admin
    always decides.
    """
    req = _get_or_404(db, leave_id)

    if req.status != LeaveStatus.pending:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("leave.already_decided"))

    warnings: list[str] = []
    if new_status == LeaveStatus.approved:
        if _overlaps_generated_schedule(db, req):
            warnings.append(t("leave.schedule_stale"))
        # Approving must never silently break flight coverage — check every
        # day of the span against the 1A+1D / 1A+2D demand and warn (admin
        # still decides; never a hard block).
        warnings.extend(_staffing_warnings(db, req))

    req.status = new_status
    db.commit()
    db.refresh(req)
    return req, warnings


def revoke(
    db: Session, leave_id: int, admin_id: int
) -> tuple[LeaveRequest, list[str]]:
    """Admin revokes a previously APPROVED leave (owner decision 2026-07-17).

    Flips the request back to rejected and — like approval — warns when the
    span overlaps an already-generated month (that schedule still shows the
    leave until the admin regenerates it).
    """
    req = _get_or_404(db, leave_id)
    if req.status != LeaveStatus.approved:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("leave.revoke_only_approved")
        )

    warnings: list[str] = []
    if _overlaps_generated_schedule(db, req):
        warnings.append(t("leave.schedule_stale"))

    req.status = LeaveStatus.rejected
    db.commit()
    db.refresh(req)
    return req, warnings


def _staffing_warnings(db: Session, req: LeaveRequest) -> list[str]:
    """Flight-coverage impact of approving this leave (role-A people only).

    For each day of the span, compare the remaining role-A staff (active,
    not already on approved leave that day, minus this requester) against the
    day's demand from the flight schedule: 1 pair → 1A+1D, 2 pairs → 1A+2D.
    Two severities:
    - remaining < max(A,D) people → the day CANNOT be covered at all;
    - remaining < A+D people → too few people for ordinary A + D coverage.
    """
    from app.models.enums import Role
    from app.services import flight_service
    from app.services.schedule_violation_checker import DEMAND

    requester = db.get(User, req.user_id)
    if requester is None or requester.role is not Role.A:
        return []  # T/M/F never count toward flight coverage

    days = [
        req.start_date + timedelta(days=i)
        for i in range((req.end_date - req.start_date).days + 1)
    ]
    pairs_by_day = flight_service.flight_pairs_map(db, days)

    role_a_ids = {
        uid
        for (uid,) in db.query(User.id).filter(
            User.role == Role.A, User.status == UserStatus.active
        )
    }
    role_a_ids.discard(req.user_id)

    # Approved leaves of OTHER role-A people overlapping the span.
    others_on_leave = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.status == LeaveStatus.approved,
            LeaveRequest.user_id.in_(role_a_ids),
            LeaveRequest.start_date <= req.end_date,
            LeaveRequest.end_date >= req.start_date,
        )
        .all()
    )

    warnings: list[str] = []
    for day in days:
        need_a, need_d = DEMAND.get(pairs_by_day.get(day, 0), (0, 0))
        if need_a + need_d == 0:
            continue
        away = {
            o.user_id
            for o in others_on_leave
            if o.start_date <= day <= o.end_date
        }
        remaining = len(role_a_ids - away)
        if remaining < max(need_a, need_d):
            warnings.append(f"{day.isoformat()}: {t('leave.staffing_impossible')}")
        elif remaining < need_a + need_d:
            warnings.append(f"{day.isoformat()}: {t('leave.staffing_short_ordinary')}")
    return warnings


def _overlaps_generated_schedule(db: Session, req: LeaveRequest) -> bool:
    """True when any month of the leave span already has a schedule row.

    The schedule only consumes approved leave at GENERATE time, so approving
    afterwards leaves the existing (draft or published) grid stale — the
    admin must regenerate that month for the leave to appear.
    """
    from app.models.schedule import MonthlySchedule  # local: avoid cycle

    months: set[tuple[int, int]] = set()
    day = req.start_date
    while day <= req.end_date:
        months.add((day.year, day.month))
        day += timedelta(days=1)
    for year, month in months:
        exists = (
            db.query(MonthlySchedule.id)
            .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
            .first()
        )
        if exists is not None:
            return True
    return False


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

    Uses leave_conflict_resolver.rank with carry_comp derived by
    schedule_history for the contested month — the same values the scheduler
    uses, so no month-close is needed for the ranking to be current.
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
    carry = {
        uid: s.carry_comp
        for uid, s in schedule_history.build_boundary_states(
            db, users, target_date.year, target_date.month
        ).items()
    }

    # Criterion 2 input: off days these users ALREADY hold (approved) around
    # the contested date — one month either side covers every 7-day block a
    # request can touch.
    window_start = target_date - timedelta(days=31)
    window_end = target_date + timedelta(days=31)
    approved = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.status == LeaveStatus.approved,
            LeaveRequest.user_id.in_(user_ids),
            LeaveRequest.start_date <= window_end,
            LeaveRequest.end_date >= window_start,
        )
        .all()
    )
    approved_off_by_user: dict[int, set[date]] = {}
    for req in approved:
        day = req.start_date
        while day <= req.end_date:
            approved_off_by_user.setdefault(req.user_id, set()).add(day)
            day += timedelta(days=1)

    return leave_conflict_resolver.rank(requests, carry, approved_off_by_user)
