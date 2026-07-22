"""Effective scheduling history used when building a new month.

Actual attendance wins over the planned schedule for the same user/day.  When
an actual row is still missing (normal while next month's draft is generated),
the planned assignment is the best available fact.  This lets the next month
honour A/D compensation and month-boundary rest rules without requiring a
manual "close month" step first.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, Role
from app.models.schedule import ShiftAssignment
from app.models.user import User
from app.services.carry_over_math import comp_balance


@dataclass(frozen=True)
class BoundaryState:
    carry_comp: int
    carry_streak: int
    previous_working: dict[date, bool]


def previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _effective_grid(
    db: Session, user_ids: set[int], cutoff: date
) -> dict[tuple[int, date], AttendanceCode]:
    """Planned history with actual attendance overlaid on top."""
    if not user_ids:
        return {}

    grid: dict[tuple[int, date], AttendanceCode] = {}
    planned = (
        db.query(ShiftAssignment)
        .filter(
            ShiftAssignment.user_id.in_(user_ids),
            ShiftAssignment.work_date <= cutoff,
        )
        .all()
    )
    for row in planned:
        grid[(row.user_id, row.work_date)] = row.code

    actual = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.user_id.in_(user_ids),
            AttendanceRecord.work_date <= cutoff,
        )
        .all()
    )
    for row in actual:
        grid[(row.user_id, row.work_date)] = row.code
    return grid


def build_boundary_states(
    db: Session, users: list[User], target_year: int, target_month: int
) -> dict[int, BoundaryState]:
    """Derive carry values immediately before ``target_year/target_month``.

    Six explicit previous-day working flags are returned because a scalar
    trailing streak cannot enforce "at least two rest days in every rolling
    seven-day window" across a month boundary.
    """
    prev_year, prev_month = previous_month(target_year, target_month)
    cutoff = date(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])
    user_ids = {u.id for u in users}
    grid = _effective_grid(db, user_ids, cutoff)

    states: dict[int, BoundaryState] = {}
    for user in users:
        records = sorted(
            (day, code)
            for (uid, day), code in grid.items()
            if uid == user.id
        )

        # Only role A earns/consumes automatic compensation.  Stored carry is a
        # fallback for legacy databases where old schedule/actual rows are absent.
        if user.role is Role.A:
            carry_comp = comp_balance(records) if records else user.carry_comp
        else:
            carry_comp = 0

        # Count a genuinely contiguous run ending on the previous month's last
        # calendar day. Missing history falls back to the legacy stored scalar.
        carry_streak = 0
        cursor = cutoff
        last_code = grid.get((user.id, cursor))
        if last_code is None:
            carry_streak = max(0, user.carry_streak)
        else:
            while True:
                code = grid.get((user.id, cursor))
                if code is None or not code.is_working:
                    break
                carry_streak += 1
                cursor -= timedelta(days=1)

        previous_working: dict[date, bool] = {}
        streak_start = cutoff - timedelta(days=max(0, carry_streak - 1))
        for offset in range(5, -1, -1):
            day = cutoff - timedelta(days=offset)
            code = grid.get((user.id, day))
            if code is not None:
                previous_working[day] = code.is_working
            else:
                # Legacy fallback can reconstruct the known trailing work run;
                # unknown older days are treated as rest rather than invented work.
                previous_working[day] = carry_streak > 0 and day >= streak_start

        states[user.id] = BoundaryState(
            carry_comp=carry_comp,
            carry_streak=carry_streak,
            previous_working=previous_working,
        )
    return states
