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
    objective_premium_off,
)
from app.scheduler.calendar_utils import month_days
from app.scheduler.role_codes import codes_for
from app.scheduler.slack_registry import SlackRegistry
from app.services.carry_over_math import premium_off_count
from app.services.schedule_violation_checker import (
    check_off_chain,
    check_rolling_rest,
    recheck,
)


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
        days,
        {1: previous},
    )

    assert any("starting 2026-06-29" in warning.message for warning in warnings)


def test_each_role_a_person_gets_two_a_days_and_near_equal_a_d() -> None:
    days = month_days(2026, 8)
    people = [PersonInput(uid, Role.A) for uid in range(1, 5)]
    out = SchedulerEngine().solve(
        SolverInput(
            year=2026,
            month=8,
            people=people,
            days=days,
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


def _fixed_grid_violations(inp: SolverInput, grid) -> list:
    """The engine's verdict on a GIVEN grid: every constraint, cells pinned.

    ``grid`` holds decision-layer codes (approved leave is ``X``).
    """
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    registry = SlackRegistry()
    constraints.add_all(model, x, inp, registry)
    for (uid, day, code), var in x.items():
        model.add(var == int(grid[(uid, day)] is code))
    model.minimize(sum(registry.penalty_terms()))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    assert solver.solve(model) == cp_model.OPTIMAL
    return registry.violations(solver)


def _restore_leave(grid, approved):
    """Persisted view: pinned cells carry their concrete leave code (AL)."""
    return {
        (uid, day): approved.get(uid, {}).get(day, code)
        for (uid, day), code in grid.items()
    }


def test_five_day_monthly_leave_is_rest_no_violation() -> None:
    """C3 / ruling R1: a 5-day monthly leave Tue 9 – Sat 13 Feb 2027 is legal
    next to X days (an off-run holding approved leave). Since owner
    2026-11-10 the leave counts as rest for the rolling 7-day rule, so the
    week no longer gets two X on top (supersedes decision #4): the person
    on leave needs fewer X than a colleague with the same role."""
    days = month_days(2027, 2)
    approved = {1: {date(2027, 2, d): AttendanceCode.AL for d in range(9, 14)}}
    inp = SolverInput(
        year=2027,
        month=2,
        people=[PersonInput(1, Role.T), PersonInput(2, Role.T)],
        days=days,
        flight_pairs={day: 0 for day in days},
        approved_off=approved,
        max_solve_seconds=10,
    )
    out = SchedulerEngine(num_workers=1).solve(inp)

    assert out.feasible and out.violations == []
    grid = _restore_leave(_grid(out), approved)
    x_count = {
        uid: sum(1 for d in days if grid[(uid, d)] is AttendanceCode.X) for uid in (1, 2)
    }
    assert x_count[1] < x_count[2], x_count
    assert recheck(
        grid=grid,
        roles={1: Role.T, 2: Role.T},
        carry_streaks={},
        days=days,
        flight_pairs={day: 0 for day in days},
    ) == []


def test_off_chain_crosses_month_boundary() -> None:
    """F8: five off days ending July plus X on 1 August is a six-day off-run.

    The engine sees July through ``PersonInput.prev_codes`` (oldest first) and
    the checker through ``prev_codes``; both flag the run at 27 July. With
    approved leave in those July days the run is exempt (ruling R1).
    """
    days = month_days(2026, 8)
    X, CD, AD, AL = (
        AttendanceCode.X, AttendanceCode.CD, AttendanceCode.AD, AttendanceCode.AL,
    )
    # 26 Jul worked, 27–31 Jul off.
    prev = (AD, X, X, CD, X, X)

    def inp_for(prev_codes):
        return SolverInput(
            year=2026,
            month=8,
            people=[PersonInput(1, Role.T, prev_codes=prev_codes)],
            days=days,
            flight_pairs={day: 0 for day in days},
            max_solve_seconds=10,
        )

    # X on 1 Aug, then a clean 5-on / 2-off rhythm.
    grid = {(1, d): X if (d.day - 1) % 7 in (0, 6) else AD for d in days}

    engine = _fixed_grid_violations(inp_for(prev), grid)
    assert [(v.rule, v.day) for v in engine] == [
        ("max_consecutive_off", date(2026, 7, 27))
    ]
    checker = check_off_chain(grid, {1: Role.T}, days, {}, prev_codes={1: prev})
    assert [(v.rule, v.day) for v in checker] == [
        ("max_consecutive_off", date(2026, 7, 27))
    ]

    # Left alone, the engine now keeps 1 August a working day.
    out = SchedulerEngine().solve(inp_for(prev))
    assert out.feasible and out.violations == []
    assert _grid(out)[(1, days[0])] is AD

    # Ruling R1: the same run holding approved leave is legal for both.
    leave = (AD, AL, AL, AL, AL, AL)
    assert _fixed_grid_violations(inp_for(leave), grid) == []
    assert check_off_chain(grid, {1: Role.T}, days, {}, prev_codes={1: leave}) == []


def test_premium_off_ignores_pinned_al() -> None:
    """F9 / ruling R2: a pinned leave on Sat/Sun is not a premium off — only X
    days the engine chooses count, like ``carry_over_math.premium_off_count``."""
    days = month_days(2026, 8)  # 1 Aug 2026 is a Saturday
    weekend = [d for d in days[:7] if d.weekday() >= 5]
    approved = {1: {d: AttendanceCode.AL for d in weekend}}
    inp = SolverInput(
        year=2026,
        month=8,
        people=[PersonInput(1, Role.T), PersonInput(2, Role.T)],
        days=days,
        flight_pairs={day: 0 for day in days},
        approved_off=approved,
    )
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    # Neither person has an engine-chosen X on a premium day; user 1 has the
    # pinned leave weekend (decision layer: X).
    for (uid, day, code), var in x.items():
        off = uid == 1 and day in weekend
        model.add(var == int(code is (AttendanceCode.X if off else AttendanceCode.AD)))
    terms = objective_premium_off.terms(model, x, inp, weight=1)
    model.minimize(sum(terms))
    solver = cp_model.CpSolver()
    assert solver.solve(model) == cp_model.OPTIMAL
    assert solver.objective_value == 0

    # Persisted grid → next month's carry agrees.
    grid = {d: AttendanceCode.AL if d in weekend else AttendanceCode.AD for d in days}
    assert premium_off_count(sorted(grid.items()), set()) == 0
