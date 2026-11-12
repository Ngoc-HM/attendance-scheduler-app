"""Shared assertion for the rest rules (owner 2026-11-12).

* W: at most 5 working days in every Mon–Sun calendar week (2 rest days a
  week, not necessarily adjacent); the week that started last month reads
  the history (a day with no history counts as not worked), the week ending
  next month counts this month's days only.
* C: no more than 5 working days in a row; one day off resets the run; a
  run carried in from last month (``carry_streak``) counts.

The rolling reading ("any 7 consecutive days") is gone.
"""

from __future__ import annotations

from datetime import date

from app.models.enums import AttendanceCode
from app.scheduler.constraints_weekly_rest import weeks


def assert_rest_rules(
    grid: dict[tuple[int, date], AttendanceCode],
    uid: int,
    days: list[date],
    previous_working: dict[date, bool] | None = None,
    carry_streak: int = 0,
) -> None:
    history = previous_working or {}
    for monday, before, inside in weeks(days):
        worked = sum(1 for d in before if history.get(d, False))
        worked += sum(1 for d in inside if grid[(uid, d)].is_working)
        assert worked <= 5, f"user {uid}: {worked} working days in the week of {monday}"
    run = carry_streak
    for d in sorted(days):
        run = run + 1 if grid[(uid, d)].is_working else 0
        assert run <= 5, f"user {uid}: {run} working days in a row up to {d}"
