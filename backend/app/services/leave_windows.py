"""Pure leave-window and classification logic (no DB, fully testable).

Business rules (locked decision #10, spec §4.3 / F-05 / F-06):
- Classification: consecutive span > 5 days (>= 6) → annual; <= 5 → monthly.
  (Customer clarification 2026-06-12: "quá 5 ngày liên tục" = more than 5.)
- Monthly window: during month M, days 1–``AUTORUN_DAY`` (default 20)
  inclusive, register for month M+1. The window closes at the end of that
  day; the autorun generates M+1's draft the following day (00:05).
  Submission outside that window for the target month → window_closed_monthly.
- Annual window: leave year is hardcoded to Y+1 (the year after today).
- Sick (S) is NOT a leave request — not validated here.
"""

from __future__ import annotations

from datetime import date

from app.core.config import settings
from app.models.enums import LeaveType


def classify(start: date, end: date) -> LeaveType:
    """Return the leave bucket based on consecutive-day span.

    A span of MORE than 5 calendar days (>= 6, inclusive on both ends) is
    annual leave; 5 or fewer is monthly leave (customer rule 2026-06-12).
    """
    span = (end - start).days + 1  # inclusive count
    return LeaveType.annual if span > 5 else LeaveType.monthly


def registration_last_day() -> int:
    """Last day of month M on which monthly leave for M+1 may be registered.

    Tied to ``settings.AUTORUN_DAY`` so the window and the autorun can never
    drift apart: the window closes at the end of this day and the draft for
    M+1 is generated the day after.
    """
    return settings.AUTORUN_DAY


def is_monthly_window_open(today: date, target_month: int, target_year: int) -> bool:
    """Return True iff today falls within the monthly-registration window.

    The window is days 1–``registration_last_day()`` (default 20) of the month
    *before* the target month.
    E.g. target = 2025-03 → window is 2025-02-01 to 2025-02-20.
    """
    # Derive the expected submission month (month before target).
    if target_month == 1:
        expected_year = target_year - 1
        expected_month = 12
    else:
        expected_year = target_year
        expected_month = target_month - 1

    return (
        today.year == expected_year
        and today.month == expected_month
        and 1 <= today.day <= registration_last_day()
    )


def is_annual_window_open(today: date, leave_start_year: int) -> bool:
    """Return True iff the leave year is exactly Y+1 (the year after today)."""
    return leave_start_year == today.year + 1
