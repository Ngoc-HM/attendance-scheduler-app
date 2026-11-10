"""Auto comp-day off (hướng B, customer 2026-06-12).

The system itself schedules last month's owed comp days (carry_comp → CD) the
following month; the person does not register them. Soft rule that yields to
flight staffing. See app/scheduler/constraints_comp_days.py.
"""

from __future__ import annotations

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import month_days
from tests.rest_invariants import assert_rest_rules


def _solve(people, days, flight_pairs=None):
    return SchedulerEngine().solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
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
    people = [PersonInput(1, Role.A, carry_comp=3)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    assert _count(_grid(out), 1, days, AttendanceCode.CD) == 3


def test_no_comp_debt_means_no_cd() -> None:
    """carry_comp=0 → the solver must never hand out CD rest (role A)."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.A, carry_comp=0)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    assert _count(_grid(out), 1, days, AttendanceCode.CD) == 0


def test_cd_is_rest_for_the_seven_day_rule() -> None:
    """Owed CDs are granted on top of the month's X target (8 Saturdays +
    Sundays in July 2026, owner 2026-11-10) and count as rest for the rolling
    7-day rule."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.A, carry_comp=2)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    grid = _grid(out)
    assert _count(grid, 1, days, AttendanceCode.CD) == 2
    assert_rest_rules(grid, 1, days)
    assert _count(grid, 1, days, AttendanceCode.X) == 8


def test_cd_counts_as_rest_not_work() -> None:
    """A CD day breaks the working streak: no consecutive-work violation fires
    even when the owed comp rest sits next to working days."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.A, carry_comp=4)]
    out = _solve(people, days)

    assert out.feasible
    assert not [v for v in out.violations if v.rule.startswith("max_consecutive")]


def test_role_t_owed_cd_is_scheduled() -> None:
    """Owner D1 (2026-11-06): holiday work earns CD for every role, so a role-T
    person owed 1 comp day gets exactly 1 CD; every other cell is AD or X."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.T, carry_comp=1)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    grid = _grid(out)
    assert _count(grid, 1, days, AttendanceCode.CD) == 1
    others = {AttendanceCode.AD, AttendanceCode.X}
    assert all(grid[(1, d)] in others for d in days if grid[(1, d)] is not AttendanceCode.CD)


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
