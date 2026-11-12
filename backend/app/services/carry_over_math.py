"""Pure carry-over math for month-close (F-14) — no DB, fully testable.

Carry values are recomputed ABSOLUTELY from the actual-record history so a
re-run of the close is idempotent (decision in phase 07): never ``+=`` against
the stored value.

    carry_comp        = CD earned − CD consumed over history           (floor 0)
                        earned: each A/D, plus each working day on a
                        public holiday from the effective date on, for
                        every role (owner D1 2026-11-06); a CD before the
                        effective date only pays back what was earned
                        before it (ruling R3, 2026-11-08)
    carry_streak      = trailing working-day run of the closed month   (§5.5)
    carry_premium_off = OFF (X) days on Sat/Sun/holiday over history    (#6)
    carry_pair_points = weekday bonus of adjacent X+X pairs, 12 months
                        (owner 2026-11-12; ``pair_points``)
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from app.models.enums import AttendanceCode
from app.scheduler.calendar_utils import trailing_work_streak
from app.scheduler.objective_off_pairing import WEEKDAY_BONUS

SATURDAY, SUNDAY = 5, 6
# Codes meaning "at work" for the consecutive-streak count (mirror the engine).
_WORK = {
    AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D, AttendanceCode.AD,
    AttendanceCode.O_D, AttendanceCode.T, AttendanceCode.B,
}


def comp_balance_from_counts(
    earned_before: int, consumed_before: int, earned_from: int, consumed_from: int
) -> int:
    """Outstanding comp days from counts split at the effective date.

    Ruling R3 (2026-11-08): consumption is counted from
    ``HOLIDAY_COMP_EFFECTIVE_FROM`` like earning. A CD before that date pays
    back only what was earned before it (A/D); a surplus of such CDs (legacy
    manual CDs) is dropped instead of eating comp earned from the date on,
    while a pre-date A/D that its own CD paid back stays paid back.
    """
    before = max(0, earned_before - consumed_before)
    return max(0, before + earned_from - consumed_from)


def comp_balance(
    records: list[tuple[date, AttendanceCode]],
    holidays: set[date],
    effective_from: date | None = None,
) -> int:
    """Outstanding comp days, the same rule for every role.

    Each A/D earns 1 CD; any working code on a public holiday earns 1 more
    (so A/D on a holiday earns 2); each CD code consumes 1. Holiday earning
    starts at ``effective_from`` (``None`` = no cut-off) so it is never
    applied retroactively; A/D earning is not date-gated. CDs before
    ``effective_from`` only consume comp earned before it (R3).
    """
    counts = [0, 0, 0, 0]  # earned_before, consumed_before, earned_from, consumed_from
    for d, c in records:
        from_date = effective_from is None or d >= effective_from
        earned = int(c is AttendanceCode.A_D) + int(
            from_date and c.is_working and d in holidays
        )
        consumed = int(c is AttendanceCode.CD)
        counts[2 if from_date else 0] += earned
        counts[3 if from_date else 1] += consumed
    return comp_balance_from_counts(*counts)


def premium_off_count(
    records: list[tuple[date, AttendanceCode]], holidays: set[date]
) -> int:
    """OFF (X) days landing on a Saturday, Sunday or holiday (#6)."""
    return sum(
        1
        for d, c in records
        if c is AttendanceCode.X and (d.weekday() in (SATURDAY, SUNDAY) or d in holidays)
    )


def pair_points(off_days: Iterable[date]) -> int:
    """Weekday-bonus points of one person's adjacent X+X pairs (owner 2026-11-12).

    ``off_days`` are the days with a genuine X (not AL/CD/S). Each pair is
    counted once, by the weekday of its first day, as the engine scores it
    (``objective_off_pairing.WEEKDAY_BONUS``: Fri+Sat 3, Sat+Sun 2, Sun+Mon
    1); a pair across a month boundary is one pair like any other.
    """
    offs = set(off_days)
    return sum(
        WEEKDAY_BONUS.get(d.weekday(), 0)
        for d in offs
        if d + timedelta(days=1) in offs
    )


def trailing_streak(month_records: list[tuple[date, AttendanceCode]]) -> int:
    """Consecutive working days ending the closed month (§5.5).

    ``month_records`` is just the closed month's cells; order-independent
    (sorted here). 0 if the last day is off.
    """
    ordered = sorted(month_records, key=lambda rc: rc[0])
    flags = [code in _WORK for _, code in ordered]
    return trailing_work_streak(flags)
