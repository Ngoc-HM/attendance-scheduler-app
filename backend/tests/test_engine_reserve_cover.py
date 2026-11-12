"""Reserve cover — 3 group-A people at work on flight days (owner 2026-11-12).

A soft preference (``objective_reserve_cover``), never a violation: the
staffing floor stays 1A+1D for one flight pair and 1A+2D for two; on top of
it a third role-A person should be at work on every flight day, unless that
would cost someone a day off below the month's X target.
"""

from __future__ import annotations

from datetime import date

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import month_days
from tests.rest_invariants import assert_rest_rules

A, D, X = AttendanceCode.A, AttendanceCode.D, AttendanceCode.X
WED = 2
FEB_2027 = month_days(2027, 2)  # 4 full weeks, 8 Sat + Sun → 8 X each
GROUP_A = (1, 2, 3, 4)


def _solve(flight_pairs: dict[date, int]):
    out = SchedulerEngine(num_workers=1).solve(
        SolverInput(
            year=2027,
            month=2,
            people=[PersonInput(u, Role.A) for u in GROUP_A],
            days=FEB_2027,
            flight_pairs=flight_pairs,
            max_solve_seconds=60.0,
        )
    )
    assert out.feasible
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for u in GROUP_A:
        assert_rest_rules(grid, u, FEB_2027)
        assert sum(1 for d in FEB_2027 if grid[(u, d)] is X) == 8, u
    return out, grid


def _at_work(grid, d: date) -> int:
    return sum(1 for u in GROUP_A if grid[(u, d)].is_working)


def test_three_at_work_on_flight_days_when_the_target_fits() -> None:
    """Flights on weekdays only (one pair, two on Wednesdays): 32 X fit on
    the 8 weekend days and a few weekdays, so every flight day — Fridays
    included, the favourite day off — keeps 3 of the 4 at work, and the
    two-pair floor (1A + 2D) holds."""
    fp = {
        d: (0 if d.weekday() >= 5 else 2 if d.weekday() == WED else 1)
        for d in FEB_2027
    }
    out, grid = _solve(fp)
    assert out.violations == []
    for d, pairs in fp.items():
        if pairs:
            assert _at_work(grid, d) >= 3, d
        if pairs == 2:
            codes = [grid[(u, d)] for u in GROUP_A]
            assert codes.count(A) >= 1 and codes.count(D) >= 2, d


def test_the_target_wins_over_the_reserve_and_nothing_is_reported() -> None:
    """One pair every day: 4 x 8 = 32 X over 28 days cannot all fall on days
    with a spare person, so some days keep only 2 at work (the floor). Every
    person still gets 8 X, and those days are not reported."""
    fp = {d: 1 for d in FEB_2027}
    out, grid = _solve(fp)
    assert out.violations == []
    at_work = [_at_work(grid, d) for d in FEB_2027]
    assert min(at_work) >= 2
    assert sum(1 for n in at_work if n == 2) >= 32 - 28, at_work
