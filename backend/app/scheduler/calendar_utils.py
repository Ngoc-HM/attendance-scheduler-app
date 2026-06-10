"""Calendar helpers for the scheduler (spec §5.1 week partition, §5.5 streak).

These are pure functions (no solver, no DB) and are unit-testable on their own.
"""

from __future__ import annotations

import calendar
from datetime import date


def month_days(year: int, month: int) -> list[date]:
    """All calendar days of ``month`` in order."""
    _, last = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, last + 1)]


def build_weeks(days: list[date]) -> list[list[date]]:
    """Partition consecutive ``days`` into Monday–Sunday weeks (§5.1).

    A single, consistent week definition is used everywhere so the "2 days off
    per week" rule (§5.3 #2) is applied uniformly. Partial weeks at the month
    boundaries are kept as their own groups.
    """
    weeks: list[list[date]] = []
    current: list[date] = []
    for d in sorted(days):
        # Monday (weekday() == 0) starts a new week.
        if current and d.weekday() == 0:
            weeks.append(current)
            current = []
        current.append(d)
    if current:
        weeks.append(current)
    return weeks


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
