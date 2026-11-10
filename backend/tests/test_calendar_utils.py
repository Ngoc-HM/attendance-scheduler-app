"""Unit tests for the scheduler's pure calendar helpers (§5.1, §5.5)."""

from __future__ import annotations

from app.scheduler.calendar_utils import (
    block_off_target,
    build_weeks,
    month_days,
    partial_block_days,
    trailing_work_streak,
)


def test_month_days_count() -> None:
    assert len(month_days(2026, 6)) == 30  # June has 30 days
    assert len(month_days(2026, 2)) == 28  # Feb 2026 (not a leap year)


def test_build_weeks_is_7_day_blocks_from_day_1() -> None:
    """Decision #7: blocks 1-7, 8-14, ... — NOT Monday-anchored weeks."""
    days = month_days(2026, 6)
    weeks = build_weeks(days)
    # Every day belongs to exactly one block.
    assert sum(len(w) for w in weeks) == len(days)
    # June 2026: four full blocks + a 2-day tail (29-30).
    assert [(w[0].day, w[-1].day) for w in weeks] == [
        (1, 7), (8, 14), (15, 21), (22, 28), (29, 30),
    ]
    # 31-day month → 3-day tail; 28-day February → exactly 4 full blocks.
    assert [len(w) for w in build_weeks(month_days(2026, 7))][-1] == 3
    assert [len(w) for w in build_weeks(month_days(2026, 2))] == [7, 7, 7, 7]


def test_block_off_target_full_block_only() -> None:
    """Full block → exactly 2 X; the leftover days have no quota (owner
    2026-11-10 — replaces the pro-rated round(len/7*2) tail)."""
    assert block_off_target(7) == 2
    for tail_len in (1, 2, 3):
        assert block_off_target(tail_len) is None


def test_partial_block_days_are_the_days_after_the_28th() -> None:
    assert [d.day for d in partial_block_days(build_weeks(month_days(2026, 11)))] == [
        29, 30,
    ]
    assert [d.day for d in partial_block_days(build_weeks(month_days(2026, 7)))] == [
        29, 30, 31,
    ]
    assert partial_block_days(build_weeks(month_days(2026, 2))) == []


def test_trailing_work_streak() -> None:
    assert trailing_work_streak([True, False, True, True]) == 2
    assert trailing_work_streak([True, True, False]) == 0
    assert trailing_work_streak([True, True, True]) == 3
    assert trailing_work_streak([]) == 0
