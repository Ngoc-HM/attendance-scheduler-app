"""Auto comp-day off (hướng B, customer 2026-06-12).

The system itself schedules last month's owed comp days (carry_comp → CD) the
following month; the person does not register them. Soft rule that yields to
flight staffing. See app/scheduler/constraints_comp_days.py.
"""

from __future__ import annotations

from datetime import date

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days


def _solve(people, days, flight_pairs=None):
    return SchedulerEngine().solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
            weeks=build_weeks(days),
            flight_pairs=flight_pairs or {d: 0 for d in days},
            max_solve_seconds=10.0,
        )
    )


def _grid(out):
    return {(a.user_id, a.day): a.code for a in out.assignments}


def _count(grid, uid, days, code) -> int:
    return sum(1 for d in days if grid[(uid, d)] is code)


def test_owed_comp_days_are_auto_scheduled() -> None:
    """carry_comp=3, no flights → solver grants exactly 3 CD, no shortfall."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.T, carry_comp=3)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    assert _count(_grid(out), 1, days, AttendanceCode.CD) == 3


def test_no_comp_debt_means_no_cd() -> None:
    """carry_comp=0 → the solver must never hand out CD rest."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.T, carry_comp=0)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    assert _count(_grid(out), 1, days, AttendanceCode.CD) == 0


def test_cd_is_on_top_of_weekly_off_quota() -> None:
    """CD does not consume the 2 X/week quota — each full week still has 2 X."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.T, carry_comp=2)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    grid = _grid(out)
    assert _count(grid, 1, days, AttendanceCode.CD) == 2
    for week in build_weeks(days):
        if len(week) == 7:  # full block target = 2 X (decision #7)
            assert sum(grid[(1, d)] is AttendanceCode.X for d in week) == 2


def test_cd_counts_as_rest_not_work() -> None:
    """A CD day breaks the working streak: no consecutive-work violation fires
    even when the owed comp rest sits next to working days."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.T, carry_comp=4)]
    out = _solve(people, days)

    assert out.feasible
    assert not [v for v in out.violations if v.rule.startswith("max_consecutive")]


def test_comp_days_yield_to_flight_staffing() -> None:
    """Over-constrained: 4 fixed staff, 2 flight pairs every day (needs 3
    working daily) AND each owed 10 comp days. Flights win — staffing stays
    fully covered while the unmet comp debt is reported as a shortfall."""
    days = month_days(2026, 7)
    people = [
        PersonInput(1, Role.A, carry_comp=10),
        PersonInput(2, Role.A, carry_comp=10),
        PersonInput(3, Role.A, carry_comp=10),
        PersonInput(4, Role.A, carry_comp=10),
    ]
    out = _solve(people, days, flight_pairs={d: 2 for d in days})

    assert out.feasible  # soft rule → never infeasible
    rules = {v.rule for v in out.violations}
    # CD yields: staffing fully met (higher weight), comp debt reported unmet.
    assert "fixed_group_staffing" not in rules
    assert "comp_day_shortfall" in rules
