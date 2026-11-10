"""Unit tests for the scheduler's pure calendar helpers (§5.1, §5.5)."""

from __future__ import annotations

from app.scheduler.calendar_utils import month_days, trailing_work_streak


def test_month_days_count() -> None:
    assert len(month_days(2026, 6)) == 30  # June has 30 days
    assert len(month_days(2026, 2)) == 28  # Feb 2026 (not a leap year)


def test_trailing_work_streak() -> None:
    assert trailing_work_streak([True, False, True, True]) == 2
    assert trailing_work_streak([True, True, False]) == 0
    assert trailing_work_streak([True, True, True]) == 3
    assert trailing_work_streak([]) == 0
