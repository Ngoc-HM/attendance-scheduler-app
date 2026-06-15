"""Automatic month-end calculations (F-14).

Closes a month and recomputes each user's carry-over for the NEXT month from
the actual-record history (``carry_over_math``). Idempotent by design: values
are absolute recomputations, so re-running yields the same result.

Per F-14: only comp-day / streak / premium-off logic — no complex annual-leave
accrual.
"""

from __future__ import annotations

import calendar
from datetime import date

from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode
from app.models.holiday import Holiday
from app.models.user import User
from app.services import carry_over_math


def _last_day(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def close_month(db: Session, year: int, month: int) -> dict:
    """F-14 — recompute carry_comp / carry_streak / carry_premium_off.

    Returns a per-user summary keyed by user id.
    """
    cutoff = _last_day(year, month)
    first_of_month = date(year, month, 1)

    holidays: set[date] = {h.day for h in db.query(Holiday).all()}
    users = db.query(User).order_by(User.id).all()

    # All actuals up to month end (history) — one query, grouped per user.
    history = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.work_date <= cutoff)
        .all()
    )
    per_user: dict[int, list[tuple[date, AttendanceCode]]] = {}
    for r in history:
        per_user.setdefault(r.user_id, []).append((r.work_date, r.code))

    summary: dict[int, dict] = {}
    for u in users:
        recs = per_user.get(u.id, [])
        month_recs = [(d, c) for d, c in recs if d >= first_of_month]

        u.carry_comp = carry_over_math.comp_balance(recs)
        u.carry_streak = carry_over_math.trailing_streak(month_recs)
        u.carry_premium_off = carry_over_math.premium_off_count(recs, holidays)
        summary[u.id] = {
            "carry_comp": u.carry_comp,
            "carry_streak": u.carry_streak,
            "carry_premium_off": u.carry_premium_off,
        }

    db.commit()
    return {"year": year, "month": month, "users": summary}


def summary(db: Session) -> dict:
    """Current carry values per user (read-only)."""
    users = db.query(User).order_by(User.id).all()
    return {
        u.id: {
            "carry_comp": u.carry_comp,
            "carry_streak": u.carry_streak,
            "carry_premium_off": u.carry_premium_off,
            "annual_leave_balance": u.annual_leave_balance,
        }
        for u in users
    }
