"""Pure leave-window and classification logic (no DB, fully testable).

Business rules (locked decision #10, spec §4.3 / F-05 / F-06):
- Classification: consecutive span > 5 days (>= 6) → annual; <= 5 → monthly.
  (Customer clarification 2026-06-12: "quá 5 ngày liên tục" = more than 5.)
- Monthly window: during month M, days 1–20 inclusive, register for month M+1.
  Submission outside that window for the target month → window_closed_monthly.
- Annual window: target leave must start in year Y+1 or later; submission must
  occur during calendar year Y (i.e. prior year).  Submitting for the current
  or past year → window_closed_annual.
- Sick (S) is NOT a leave request — not validated here.
"""

from __future__ import annotations

from datetime import date

from app.models.enums import LeaveType


def classify(start: date, end: date) -> LeaveType:
    """Return the leave bucket based on consecutive-day span.

    A span of MORE than 5 calendar days (>= 6, inclusive on both ends) is
    annual leave; 5 or fewer is monthly leave (customer rule 2026-06-12).
    """
    span = (end - start).days + 1  # inclusive count
    return LeaveType.annual if span > 5 else LeaveType.monthly


def is_monthly_window_open(today: date, target_month: int, target_year: int) -> bool:
    """Return True iff today falls within the monthly-registration window.

    The window is days 1–20 of the month *before* the target month.
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
        and 1 <= today.day <= 20
    )


def is_annual_window_open(today: date, leave_start_year: int) -> bool:
    """Return True iff today falls within the annual-leave registration window.

    Annual leave for year Y+1 must be submitted during calendar year Y
    (i.e. today.year == leave_start_year - 1).
    """
    return today.year == leave_start_year - 1
