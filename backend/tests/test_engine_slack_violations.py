"""Decision #2 — the always-feasible slack architecture (§5.6).

Every over-constrained scenario must still return a complete schedule, with
the broken rule reported as a Violation carrying enough metadata (rule, day,
user) for the admin to act — never a bare "infeasible".
"""

from __future__ import annotations

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days


def _solve(people, days, flight_pairs=None, approved_off=None):
    return SchedulerEngine().solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
            weeks=build_weeks(days),
            flight_pairs=flight_pairs or {d: 0 for d in days},
            approved_off=approved_off or {},
            max_solve_seconds=15.0,
        )
    )


def test_zero_slack_when_fully_staffed() -> None:
    """Weights sanity: with enough people the solver never buys slack."""
    days = month_days(2026, 6)
    people = [
        PersonInput(1, Role.M), PersonInput(2, Role.M),
        PersonInput(3, Role.T), PersonInput(4, Role.T), PersonInput(5, Role.T),
        PersonInput(6, Role.A), PersonInput(7, Role.A),
        PersonInput(8, Role.A), PersonInput(9, Role.A),
    ]
    out = _solve(people, days, flight_pairs={d: 2 for d in days})
    assert out.feasible and out.violations == []


def test_violations_carry_rule_day_and_user_metadata() -> None:
    days = month_days(2026, 6)[:7]
    pinned = {d: AttendanceCode.AL for d in days}
    out = _solve([PersonInput(1, Role.T)], days, approved_off={1: pinned})

    assert out.feasible and out.violations
    v = out.violations[0]
    assert v.rule and v.message
    assert v.user_id == 1
    assert v.day is not None


def test_full_grid_returned_even_when_rules_break() -> None:
    """A schedule cell exists for every (person, day) regardless of slack."""
    days = month_days(2026, 6)[:14]
    people = [PersonInput(6, Role.A), PersonInput(7, Role.A)]
    out = _solve(people, days, flight_pairs={d: 2 for d in days})

    assert out.feasible
    cells = {(a.user_id, a.day) for a in out.assignments}
    assert cells == {(p.user_id, d) for p in people for d in days}
    assert out.violations  # 2 people cannot cover demand of 3
