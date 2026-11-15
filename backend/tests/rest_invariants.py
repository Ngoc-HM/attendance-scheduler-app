"""Shared maximum-five-consecutive-work assertion.

Monthly quota is checked separately with approval metadata; there is no
calendar-week or rolling-seven work quota.
"""

from __future__ import annotations

from datetime import date

from app.models.enums import AttendanceCode


def assert_rest_rules(
    grid: dict[tuple[int, date], AttendanceCode],
    uid: int,
    days: list[date],
    previous_working: dict[date, bool] | None = None,
    carry_streak: int = 0,
) -> None:
    run = carry_streak
    for d in sorted(days):
        run = run + 1 if grid[(uid, d)].is_working else 0
        assert run <= 5, f"user {uid}: {run} working days in a row up to {d}"
