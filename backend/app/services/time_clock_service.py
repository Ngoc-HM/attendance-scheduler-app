"""Time-clock business logic (check-in / check-out, owner request 2026-07-09).

Own-data only: every function takes the AUTHENTICATED user's id — callers must
never pass another user's id (endpoints derive it from the token). Timestamps
are stored tz-aware UTC; the DAY a punch belongs to is bucketed in the
operation's business timezone (``settings.TIMEZONE``, Frankfurt — spec §2)
so a 00:30 local check-in does not land on yesterday's row.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.business_time import business_now, business_today, local_hm
from app.core.config import settings
from app.core.i18n import t
from app.models.enums import AttendanceCode, Role, ScheduleStatus, UserStatus
from app.models.schedule import MonthlySchedule
from app.models.time_clock import TimeClockEntry
from app.models.user import User
from app.services import attendance_service


def _today() -> date:
    """The business day in ``settings.TIMEZONE`` (never a hard-coded zone)."""
    return business_today()


def _get_entry(db: Session, user_id: int, day: date) -> TimeClockEntry | None:
    return (
        db.query(TimeClockEntry)
        .filter(
            TimeClockEntry.user_id == user_id,
            TimeClockEntry.work_date == day,
        )
        .one_or_none()
    )


def check_in(db: Session, user_id: int) -> TimeClockEntry:
    """Record today's check-in; 409 if already checked in."""
    today = _today()  # read once: the lookup and the new row share one day
    entry = _get_entry(db, user_id, today)
    if entry is not None and entry.check_in_at is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("clock.already_checked_in")
        )
    if entry is None:
        entry = TimeClockEntry(user_id=user_id, work_date=today)
        db.add(entry)
    entry.check_in_at = datetime.now(UTC)
    try:
        db.commit()
    except IntegrityError as exc:  # double-tap race on uq_time_clock_cell
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("clock.already_checked_in")
        ) from exc
    db.refresh(entry)
    return entry


def check_out(db: Session, user_id: int) -> TimeClockEntry:
    """Record today's check-out; requires a prior check-in.

    Checking out again moves the check-out to now: the latest one is the
    day's end (someone who checked out, then went back to work, checks out
    once more). Same rule as the owner's company_management time clock.
    """
    entry = _get_entry(db, user_id, _today())
    if entry is None or entry.check_in_at is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("clock.not_checked_in")
        )
    entry.check_out_at = datetime.now(UTC)
    db.commit()
    db.refresh(entry)
    return entry


def now_local() -> dict:
    """The business clock right now, for the app: date and HH:MM in
    ``settings.TIMEZONE`` (the app never uses its device clock for punches)."""
    now = business_now()
    return {
        "date": now.date(),
        "time": now.strftime("%H:%M"),
        "timezone": settings.TIMEZONE,
    }


def get_today(db: Session, user_id: int) -> TimeClockEntry | None:
    """Today's entry (or None) — lets the client render current clock state."""
    return _get_entry(db, user_id, _today())


def list_month_for_user(
    db: Session, user_id: int, year: int, month: int
) -> list[TimeClockEntry]:
    """Own entries of the month, oldest first."""
    first = date(year, month, 1)
    last = (
        date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    )
    return (
        db.query(TimeClockEntry)
        .filter(
            TimeClockEntry.user_id == user_id,
            TimeClockEntry.work_date >= first,
            TimeClockEntry.work_date < last,
        )
        .order_by(TimeClockEntry.work_date)
        .all()
    )


# --- admin: everyone's month and corrections --------------------------------

def list_month_all(
    db: Session, year: int, month: int
) -> list[tuple[TimeClockEntry, User]]:
    """Every person's entries of the month with their user, by day then code."""
    first = date(year, month, 1)
    last = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    rows = (
        db.query(TimeClockEntry, User)
        .join(User, User.id == TimeClockEntry.user_id)
        .filter(TimeClockEntry.work_date >= first, TimeClockEntry.work_date < last)
        .order_by(TimeClockEntry.work_date, User.code, User.id)
        .all()
    )
    return [(entry, user) for entry, user in rows]


def _at(day: date, local: time) -> datetime:
    """``local`` on ``day`` in the business timezone, as a UTC instant."""
    zone = ZoneInfo(settings.TIMEZONE)
    return datetime.combine(day, local.replace(tzinfo=None), zone).astimezone(UTC)


def correct(
    db: Session,
    user_id: int,
    day: date,
    check_in: time,
    check_out: time | None,
    corrected_by: int,
) -> TimeClockEntry:
    """Set one person's punches for a day (creates the day when missing).

    Check-out must come after check-in on the same day; a day in the future
    cannot be recorded.
    """
    if db.get(User, user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
    if day > _today():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("clock.future_day")
        )
    if check_out is not None and check_out <= check_in:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("clock.out_before_in")
        )
    entry = _get_entry(db, user_id, day)
    if entry is None:
        entry = TimeClockEntry(user_id=user_id, work_date=day)
        db.add(entry)
    entry.check_in_at = _at(day, check_in)
    entry.check_out_at = None if check_out is None else _at(day, check_out)
    entry.corrected_by = corrected_by
    db.commit()
    db.refresh(entry)
    return entry


# --- admin board: the punches read against the month's attendance codes -----

# Codes that mean the person was due at work and should have punched.
# B (business trip) is work away from the station, so no punch is expected.
DUE_AT_WORK = {
    AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D, AttendanceCode.AD,
    AttendanceCode.O_D, AttendanceCode.T,
}


def board(db: Session, year: int, month: int) -> list[dict]:
    """Each (person, day) of the month the admin should look at.

    The published roster is each person's schedule (owner 2026-11-13).
    ``status`` reads the punches: ``working`` (today, not checked out yet),
    ``missed_out`` (a past day without check-out), ``absent`` (due at work,
    no check-in), ``off_day`` (punched on a day off), ``ok``.

    ``tint`` is what the admin's grids paint on the day:
    ``adjusted`` (light yellow) — the admin changed that day after hearing
    from the person: a manually edited roster cell (edit, swap, sick cover)
    or an actual the admin recorded differently from the roster (S, AL…);
    ``missing`` (light red) — a past day due at work by the published roster
    with no check-in or no check-out, and not adjusted. A month that is not
    published paints nothing. The admin account is left out.
    """
    today = _today()
    schedule = (
        db.query(MonthlySchedule)
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
        .one_or_none()
    )
    published = (
        schedule is not None and schedule.status is ScheduleStatus.published
    )
    plan = (
        {(a.user_id, a.work_date): a for a in schedule.assignments}
        if published and schedule is not None
        else {}
    )
    actuals = {
        (r.user_id, r.work_date): r
        for r in attendance_service.list_month(db, year, month)
    }
    staff = {
        u.id
        for u in db.query(User).filter(
            User.status == UserStatus.active, User.role != Role.M
        )
    }
    punches = {
        (entry.user_id, entry.work_date): entry
        for entry, user in list_month_all(db, year, month)
        if user.role is not Role.M
    }

    def due_code(key: tuple[int, date]) -> AttendanceCode | None:
        if key in plan:
            return plan[key].code
        actual = actuals.get(key)
        return actual.code if actual is not None else None

    def adjusted(key: tuple[int, date]) -> bool:
        cell = plan.get(key)
        if cell is None:
            return False
        actual = actuals.get(key)
        return cell.is_manual_override or (
            actual is not None
            and actual.recorded_by is not None
            and actual.code is not cell.code
        )

    cells: list[dict] = []
    days = set(punches) | {k for k in (*plan, *actuals) if k[0] in staff}
    for key in sorted(days, key=lambda k: (k[1], k[0])):
        entry = punches.get(key)
        code = due_code(key)
        if entry is None:
            status_ = "absent" if code in DUE_AT_WORK and key[1] < today else None
        elif entry.check_out_at is None:
            status_ = "working" if key[1] >= today else "missed_out"
        elif code not in DUE_AT_WORK:
            status_ = "off_day"
        else:
            status_ = "ok"
        tint = None
        if adjusted(key):
            tint = "adjusted"
        elif published and status_ in ("absent", "missed_out"):
            tint = "missing"
        if entry is None and status_ is None and tint is None:
            continue
        cells.append({
            "user_id": key[0],
            "work_date": key[1],
            "check_in_local": local_hm(entry.check_in_at) if entry else None,
            "check_out_local": local_hm(entry.check_out_at) if entry else None,
            "corrected": entry is not None and entry.corrected_by is not None,
            "status": status_,
            "tint": tint,
        })
    return cells
