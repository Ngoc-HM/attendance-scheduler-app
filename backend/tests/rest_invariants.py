"""Shared assertions for the rest rules (owner 2026-11-10).

The month is no longer cut into 7-day blocks; what every plan must show is:
no run of 6 working days, and at most 5 working days in every rolling 7
calendar days (history before the month included; a day with no history
counts as not worked).
"""

from __future__ import annotations

from datetime import date, timedelta

from app.models.enums import AttendanceCode


def assert_rest_rules(
    grid: dict[tuple[int, date], AttendanceCode],
    uid: int,
    days: list[date],
    previous_working: dict[date, bool] | None = None,
) -> None:
    days = sorted(days)
    history = previous_working or {}
    before = [days[0] - timedelta(days=n) for n in range(6, 0, -1)]
    working = [history.get(d, False) for d in before] + [
        grid[(uid, d)].is_working for d in days
    ]
    timeline = before + days
    for i in range(len(working) - 5):
        assert not all(working[i : i + 6]), f"user {uid}: 6 working days from {timeline[i]}"
    for i in range(len(working) - 6):
        assert sum(working[i : i + 7]) <= 5, f"user {uid}: < 2 rest in 7 days from {timeline[i]}"
