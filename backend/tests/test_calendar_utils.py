"""Unit tests for the scheduler's pure calendar helpers (§5.1, §5.5)."""

from __future__ import annotations

from app.scheduler.calendar_utils import (
    build_weeks,
    month_days,
    trailing_work_streak,
)


def test_month_days_count() -> None:
    assert len(month_days(2026, 6)) == 30  # June has 30 days
    assert len(month_days(2026, 2)) == 28  # Feb 2026 (not a leap year)


def test_build_weeks_covers_all_days_and_breaks_on_monday() -> None:
    days = month_days(2026, 6)
    weeks = build_weeks(days)
    # Every day belongs to exactly one week.
    assert sum(len(w) for w in weeks) == len(days)
    # Every week after the first starts on a Monday.
    for week in weeks[1:]:
        assert week[0].weekday() == 0


def test_trailing_work_streak() -> None:
    assert trailing_work_streak([True, False, True, True]) == 2
    assert trailing_work_streak([True, True, False]) == 0
    assert trailing_work_streak([True, True, True]) == 3
    assert trailing_work_streak([]) == 0
