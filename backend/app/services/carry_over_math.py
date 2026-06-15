"""Pure carry-over math for month-close (F-14) — no DB, fully testable.

Carry values are recomputed ABSOLUTELY from the actual-record history so a
re-run of the close is idempotent (decision in phase 07): never ``+=`` against
the stored value.

    carry_comp        = A/D earned − CD consumed over history          (floor 0)
    carry_streak      = trailing working-day run of the closed month   (§5.5)
    carry_premium_off = OFF (X) days on Sat/Sun/holiday over history    (#6)
"""

from __future__ import annotations

from datetime import date

from app.models.enums import AttendanceCode
from app.scheduler.calendar_utils import trailing_work_streak

SATURDAY, SUNDAY = 5, 6
# Codes meaning "at work" for the consecutive-streak count (mirror the engine).
_WORK = {
    AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D, AttendanceCode.AD,
    AttendanceCode.O_D, AttendanceCode.T, AttendanceCode.B,
}


def comp_balance(records: list[tuple[date, AttendanceCode]]) -> int:
    """Outstanding comp days: each A/D earns 1 CD; each CD code consumes 1."""
    earned = sum(1 for _, c in records if c is AttendanceCode.A_D)
    consumed = sum(1 for _, c in records if c is AttendanceCode.CD)
    return max(0, earned - consumed)


def premium_off_count(
    records: list[tuple[date, AttendanceCode]], holidays: set[date]
) -> int:
    """OFF (X) days landing on a Saturday, Sunday or holiday (#6)."""
    return sum(
        1
        for d, c in records
        if c is AttendanceCode.X and (d.weekday() in (SATURDAY, SUNDAY) or d in holidays)
    )


def trailing_streak(month_records: list[tuple[date, AttendanceCode]]) -> int:
    """Consecutive working days ending the closed month (§5.5).

    ``month_records`` is just the closed month's cells; order-independent
    (sorted here). 0 if the last day is off.
    """
    ordered = sorted(month_records, key=lambda rc: rc[0])
    flags = [code in _WORK for _, code in ordered]
    return trailing_work_streak(flags)
