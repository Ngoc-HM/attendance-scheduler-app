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
    22–28, 29–end of the month — NOT calendar Mon–Sun weeks (owner
    re-confirmed 2026-11-06, D2). Only the final block can be partial; it
    carries no off-day quota (``block_off_target``, owner 2026-11-10).
    """
    ordered = sorted(days)
    blocks: dict[int, list[date]] = {}
    for d in ordered:
        blocks.setdefault((d.day - 1) // 7, []).append(d)
    return [blocks[k] for k in sorted(blocks)]


FULL_BLOCK_LEN = 7
FULL_BLOCK_OFF = 2  # §5.3 #2 — exactly 2 genuine X per full 7-day block


def block_off_target(block_len: int) -> int | None:
    """Required genuine OFF (X) days for a block of ``block_len`` days.

    A full 7-day block needs exactly 2 (§5.3 #2). A partial block — the
    leftover days 29–end of the month — has NO quota (``None``): the customer
    has no such rule (owner 2026-11-10). The old pro-rated target
    (``round(len/7*2)`` → 1 X on a 2–3-day tail) forced every group-A person
    off there and left two-pair flight days short. People stay protected on
    those days by max-5-consecutive-working and the rolling-7-day rest rule.
    """
    if block_len >= FULL_BLOCK_LEN:
        return FULL_BLOCK_OFF
    return None


def partial_block_days(weeks: list[list[date]]) -> list[date]:
    """Days of the blocks shorter than 7 days (no off-day quota there)."""
    return [d for block in weeks if block_off_target(len(block)) is None for d in block]


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
