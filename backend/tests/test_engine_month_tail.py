"""Leftover days of a month (29–end) carry no off-day quota (owner 2026-11-10).

The 7-day blocks 1–7 … 22–28 keep "exactly 2 genuine X"; the days after the
28th form a partial block with NO quota. They are ordinary working days: a
soft objective (``objective_tail_off``) keeps the engine from handing out free
days off there, while the max-5-consecutive and rolling-7-day rest rules still
protect people and may require an X there — that X is not a violation.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days

X = AttendanceCode.X


def _solve(people, days, flight_pairs, seconds=20.0):
    return SchedulerEngine(num_workers=1).solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
            weeks=build_weeks(days),
            flight_pairs=flight_pairs,
            max_solve_seconds=seconds,
        )
    )


def _grid(out):
    return {(a.user_id, a.day): a.code for a in out.assignments}


def _assert_rest_invariants(grid, uid, days) -> None:
    """No run of 6 working days; every 7-day window inside the month has
    at least 2 rest days (no history → the days before the month are rest)."""
    working = [grid[(uid, d)].is_working for d in days]
    for i in range(len(days) - 5):
        assert not all(working[i : i + 6]), f"user {uid}: 6-day run from {days[i]}"
    for i in range(len(days) - 6):
        assert sum(working[i : i + 7]) <= 5, f"user {uid}: window from {days[i]}"


def _assert_full_blocks_two_x(grid, uid, days) -> None:
    for block in build_weeks(days):
        if len(block) == 7:
            got = sum(1 for d in block if grid[(uid, d)] is X)
            assert got == 2, f"user {uid} block {block[0]}: {got} X"


def test_two_flight_pairs_on_leftover_days_are_fully_staffed() -> None:
    """November 2026 case: 2 pairs on the 29th and 30th need 3 of the 4
    group-A people each day. The old pro-rated tail quota (1 X each) forced
    two flight_staffing violations; without a tail quota there are none."""
    days = month_days(2026, 11)
    tail = [d for d in days if d.day > 28]
    flight_pairs = {d: (2 if d in tail else 1) for d in days}
    people = [PersonInput(u, Role.A) for u in (1, 2, 3, 4)]
    out = _solve(people, days, flight_pairs)

    assert out.feasible
    rules = [(v.rule, v.day) for v in out.violations]
    assert not [r for r in rules if r[0] == "flight_staffing"], rules
    assert not [r for r in rules if r[0] == "two_days_off_per_week"], rules
    assert not out.violations, rules

    grid = _grid(out)
    for d in tail:
        working = sum(1 for p in people if grid[(p.user_id, d)].is_working)
        assert working >= 3, f"{d}: {working} working"
    for p in people:
        _assert_full_blocks_two_x(grid, p.user_id, days)
        _assert_rest_invariants(grid, p.user_id, days)


@pytest.mark.parametrize("month", [6, 7])  # 2-day tail (29–30), 3-day (29–31)
def test_roles_without_staffing_floor_get_no_free_tail_off(month: int) -> None:
    """F and M (and T) have no flight floor: with no quota on the leftover
    days the engine still keeps them working there when no rest rule needs a
    day off (block 22–28's X can sit late enough to cover the tail)."""
    days = month_days(2026, month)
    people = [PersonInput(1, Role.F), PersonInput(2, Role.M), PersonInput(3, Role.T)]
    out = _solve(people, days, {d: 0 for d in days})

    assert out.feasible and not out.violations
    grid = _grid(out)
    for p in people:
        tail_x = [d for d in days if d.day > 28 and grid[(p.user_id, d)] is X]
        assert tail_x == [], f"user {p.user_id}: free X on {tail_x}"
        _assert_full_blocks_two_x(grid, p.user_id, days)
        _assert_rest_invariants(grid, p.user_id, days)


def test_rest_rules_still_put_an_off_day_on_the_leftover_days() -> None:
    """Block 22–28 has no flights on the 22nd/23rd and 2 pairs on 24–28, so
    each of the 3 group-A people takes both weekly X on 22/23 and works
    24–28. A 6th working day and a 7-day window with < 2 rest would follow,
    so the rest rules put X on both the 29th and the 30th — legitimately:
    no violation is reported for those days off."""
    days = month_days(2026, 6)
    busy = {date(2026, 6, d) for d in range(24, 29)}
    flight_pairs = {d: (2 if d in busy else 0) for d in days}
    people = [PersonInput(u, Role.A) for u in (1, 2, 3)]
    out = _solve(people, days, flight_pairs)

    assert out.feasible
    assert not out.violations, [(v.rule, v.day) for v in out.violations]
    grid = _grid(out)
    for p in people:
        for d in busy:
            assert grid[(p.user_id, d)].is_working
        assert grid[(p.user_id, date(2026, 6, 29))] is X
        assert grid[(p.user_id, date(2026, 6, 30))] is X
        _assert_full_blocks_two_x(grid, p.user_id, days)
        _assert_rest_invariants(grid, p.user_id, days)

