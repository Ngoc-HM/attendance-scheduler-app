"""Automatic month-end calculations (F-14).

Closes a month and persists each user's carry-over for the NEXT month. The
values come from ``schedule_history.build_boundary_states`` (planned schedule
with actual attendance overlaid) — the single source the scheduler and the
leave-conflict ranking also read. The stored columns are a snapshot persisted
at month close (for reporting); the scheduler derives live values, so a later
edit to the closed month shows up there before any re-close. Idempotent by
design: values are absolute recomputations, so re-running yields the same
result.

Per F-14: only comp-day / streak / premium-off logic — no complex annual-leave
accrual.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.user import User
from app.services import schedule_autorun, schedule_history


def close_month(db: Session, year: int, month: int) -> dict:
    """F-14 — persist carry_comp / carry_streak / carry_premium_off.

    Returns a per-user summary keyed by user id.
    """
    ny, nm = schedule_autorun.next_month(date(year, month, 1))
    users = db.query(User).order_by(User.id).all()
    states = schedule_history.build_boundary_states(db, users, ny, nm)

    summary: dict[int, dict] = {}
    for u in users:
        state = states[u.id]
        u.carry_comp = state.carry_comp
        u.carry_streak = state.carry_streak
        u.carry_premium_off = state.carry_premium_off
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
        }
        for u in users
    }
