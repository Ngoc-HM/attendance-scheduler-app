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
    """Partition ``days`` into 7-day blocks anchored at day 1 (decision #7).

    A "week" for the 2-days-off rule (§5.3 #2) is days 1–7, 8–14, 15–21,
    22–28, 29–end of the month — NOT calendar Mon–Sun weeks. Only the final
    block can be partial; its off-day target is pro-rated via
    ``partial_block_off_target``. Confirm-with-customer flag in plan.md.
    """
    ordered = sorted(days)
    blocks: dict[int, list[date]] = {}
    for d in ordered:
        blocks.setdefault((d.day - 1) // 7, []).append(d)
    return [blocks[k] for k in sorted(blocks)]


def partial_block_off_target(block_len: int) -> int:
    """Required OFF (X) days for a block of ``block_len`` days (decision #7).

    Full 7-day block → 2; partial final block pro-rates: round(len/7*2).
    E.g. 2-day tail → 1, 3-day tail → 1, 1-day tail → 0.
    """
    if block_len >= 7:
        return 2
    return round(block_len / 7 * 2)


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
