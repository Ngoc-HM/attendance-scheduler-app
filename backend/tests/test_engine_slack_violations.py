"""Decision #2 — the always-feasible slack architecture (§5.6).

Every over-constrained scenario must still return a complete schedule, with
the broken rule reported as a Violation carrying enough metadata (rule, day,
user) for the admin to act — never a bare "infeasible".
"""

from __future__ import annotations

from datetime import timedelta

from app.models.enums import Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import month_days


def _solve(people, days, flight_pairs=None, approved_off=None):
    return SchedulerEngine().solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
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
        PersonInput(10, Role.A), PersonInput(11, Role.A),
    ]
    out = _solve(people, days, flight_pairs={d: 2 for d in days})
    assert out.feasible and out.violations == []


def test_violations_carry_rule_day_and_user_metadata() -> None:
    # November 2026 starts on a Sunday: Mon 26 – Sat 31 Oct worked (history)
    # already make 6 working days in the week of 26 Oct, whatever day 1
    # holds (rule W, owner 2026-11-12).
    # (A full week of approved leave no longer does: ruling R1 exempts it.)
    days = month_days(2026, 11)[:7]
    worked = {days[0] - timedelta(days=n): True for n in range(1, 7)}
    out = SchedulerEngine().solve(
        SolverInput(
            year=2026,
            month=11,
            people=[PersonInput(1, Role.T, carry_streak=6)],
            days=days,
            flight_pairs={d: 0 for d in days},
            previous_working={1: worked},
            max_solve_seconds=15.0,
        )
    )

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
