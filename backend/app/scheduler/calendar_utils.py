"""Calendar helpers for the scheduler (spec §5.1 month days, §5.5 streak).

These are pure functions (no solver, no DB) and are unit-testable on their own.
The month is no longer cut into 7-day blocks (owner 2026-11-10): rest is
governed by the rolling 7-day rule, which needs no partition.
"""

from __future__ import annotations

import calendar
from datetime import date


def month_days(year: int, month: int) -> list[date]:
    """All calendar days of ``month`` in order."""
    _, last = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, last + 1)]


def trailing_work_streak(working_flags: list[bool]) -> int:
    """Count trailing working days (used to compute ``carry_streak``, §5.5).

    ``working_flags`` is ordered by date; returns the length of the run of
    ``True`` ending the list (0 if the last day is off).
    """
    streak = 0
    for flag in reversed(working_flags):
        if not flag:
            break
        streak += 1
    return streak
