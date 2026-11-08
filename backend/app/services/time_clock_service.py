"""Time-clock business logic (check-in / check-out, owner request 2026-07-09).

Own-data only: every function takes the AUTHENTICATED user's id — callers must
never pass another user's id (endpoints derive it from the token). Timestamps
are stored tz-aware UTC; the DAY a punch belongs to is bucketed in the
operation's business timezone (``settings.TIMEZONE``, Frankfurt — spec §2)
so a 00:30 local check-in does not land on yesterday's row.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.business_time import business_today
from app.core.i18n import t
from app.models.time_clock import TimeClockEntry


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
    """Record today's check-out; requires a prior check-in, no overwrite."""
    entry = _get_entry(db, user_id, _today())
    if entry is None or entry.check_in_at is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("clock.not_checked_in")
        )
    if entry.check_out_at is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("clock.already_checked_out")
        )
    entry.check_out_at = datetime.now(UTC)
    db.commit()
    db.refresh(entry)
    return entry


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
