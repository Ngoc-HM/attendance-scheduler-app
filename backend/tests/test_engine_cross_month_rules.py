"""Regression tests for rolling rest and per-person role-A balance."""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler import (
    PersonInput,
    SchedulerEngine,
    SolverInput,
    constraints,
    constraints_off_chain,
)
from app.scheduler.calendar_utils import build_weeks, month_days
from app.scheduler.role_codes import codes_for
from app.scheduler.slack_registry import SlackRegistry
from app.services.schedule_violation_checker import check_rolling_rest


def _grid(out):
    return {(item.user_id, item.day): item.code for item in out.assignments}


def test_rolling_seven_days_crosses_month_boundary() -> None:
    days = month_days(2026, 7)
    previous = {
        days[0] - timedelta(days=offset): offset in {1, 2}
        for offset in range(6, 0, -1)
    }
    out = SchedulerEngine().solve(
        SolverInput(
            year=2026,
            month=7,
            people=[PersonInput(1, Role.T, carry_streak=2)],
            days=days,
            weeks=build_weeks(days),
            flight_pairs={day: 0 for day in days},
            previous_working={1: previous},
            max_solve_seconds=10,
        )
    )

    assert out.feasible and not out.violations
    grid = _grid(out)
    combined = [previous[d] for d in sorted(previous)] + [
        grid[(1, day)].is_working for day in days
    ]
    assert all(
        sum(combined[start : start + 7]) <= 5
        for start in range(len(combined) - 6)
    )
    # Two working days were carried in, so five more consecutive working days
    # at the start of July is specifically impossible.
    assert sum(grid[(1, day)].is_working for day in days[:5]) <= 3


def test_manual_recheck_flags_cross_month_rolling_rest() -> None:
    days = month_days(2026, 7)
    previous = {
        days[0] - timedelta(days=offset): offset in {1, 2}
        for offset in range(6, 0, -1)
    }
    grid = {
        (1, day): AttendanceCode.AD if day in days[:5] else AttendanceCode.X
        for day in days
    }

    warnings = check_rolling_rest(
        grid,
        {1: Role.T},
        build_weeks(days),
        {1: previous},
    )

    assert any("starting 2026-06-29" in warning for warning in warnings)


def test_each_role_a_person_gets_two_a_days_and_near_equal_a_d() -> None:
    days = month_days(2026, 8)
    people = [PersonInput(uid, Role.A) for uid in range(1, 5)]
    out = SchedulerEngine().solve(
        SolverInput(
            year=2026,
            month=8,
            people=people,
            days=days,
            weeks=build_weeks(days),
            # Equal A/D flight demand leaves the solver free to make each
            # person's monthly A and D totals genuinely near-equal.
            flight_pairs={day: 1 for day in days},
            max_solve_seconds=20,
        )
    )

    assert out.feasible and not out.violations
    grid = _grid(out)
    for person in people:
        pure_a = sum(grid[(person.user_id, day)] is AttendanceCode.A for day in days)
        total_a = sum(
            grid[(person.user_id, day)] is AttendanceCode.A
            for day in days
        )
        total_d = sum(
            grid[(person.user_id, day)] is AttendanceCode.D
            for day in days
        )
        assert pure_a >= 2
        assert abs(total_a - total_d) <= 1
        assert all(
            grid[(person.user_id, day)] is not AttendanceCode.A_D for day in days
        )


def test_cd_counts_toward_consecutive_off_limit() -> None:
    """A solver-placed CD next to five X is a six-day off-run (B7).

    The post-edit recheck already counts CD as OFF; the engine must agree, so
    five X followed by the owed comp day breaks "no more than 5 off in a row".
    """
    days = month_days(2026, 9)
    person = PersonInput(1, Role.A, carry_comp=1)
    inp = SolverInput(
        year=2026,
        month=9,
        people=[person],
        days=days,
        weeks=build_weeks(days),
        flight_pairs={day: 0 for day in days},
    )
    model = cp_model.CpModel()
    x = {
        (person.user_id, day, code): model.new_bool_var(f"x_{day}_{code.name}")
        for day in days
        for code in codes_for(person.role)
    }
    constraints.one_status_per_day(model, x, inp)
    off_run = [date(2026, 9, d) for d in range(7, 12)]
    comp_day = date(2026, 9, 12)
    for day in days:
        if day in off_run:
            code = AttendanceCode.X
        elif day == comp_day:
            code = AttendanceCode.CD
        else:
            code = AttendanceCode.A
        model.add(x[(person.user_id, day, code)] == 1)
    registry = SlackRegistry()
    constraints_off_chain.add(model, x, inp, registry)
    model.minimize(sum(registry.penalty_terms()))

    solver = cp_model.CpSolver()
    assert solver.solve(model) == cp_model.OPTIMAL
    violations = registry.violations(solver)
    assert [(v.rule, v.day) for v in violations] == [
        ("max_consecutive_off", date(2026, 9, 7))
    ]
