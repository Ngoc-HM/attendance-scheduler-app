"""Calendar helpers for the scheduler (spec §5.1 month days, §5.5 streak).

These are pure functions (no solver, no DB) and are unit-testable on their own.
The month is no longer cut into 7-day blocks (owner 2026-11-10): rest is
governed by Mon–Sun calendar weeks across months and "no more than 5
working days in a row" (owner 2026-11-12), which need no month partition.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta


def month_days(year: int, month: int) -> list[date]:
    """All calendar days of ``month`` in order."""
    _, last = calendar.monthrange(year, month)
    return [date(year, month, d) for d in range(1, last + 1)]


def carry_days(year: int, month: int) -> list[date]:
    """Days of the NEXT month up to the Sunday that ends ``month``'s last
    week (owner 2026-11-18): generating a month also plans them. A month
    that ends on a Sunday has none."""
    last = month_days(year, month)[-1]
    return [last + timedelta(days=n) for n in range(1, 7 - last.weekday())]


def window_days(year: int, month: int) -> list[date]:
    """The month's generation window: its days, then its carry days."""
    return month_days(year, month) + carry_days(year, month)


def month_groups(days: list[date]) -> list[list[date]]:
    """``days`` sorted and split by calendar month, in order."""
    groups: dict[tuple[int, int], list[date]] = {}
    for d in sorted(days):
        groups.setdefault((d.year, d.month), []).append(d)
    return list(groups.values())


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
