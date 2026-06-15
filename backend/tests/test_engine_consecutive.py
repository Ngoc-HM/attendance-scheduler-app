"""§5.3 #3 + §5.5 — max 5 consecutive working days: bind + carry + slack."""

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


def _max_run(grid, user_id, days) -> int:
    run = best = 0
    for d in days:
        run = run + 1 if grid[(user_id, d)] is not AttendanceCode.X else 0
        best = max(best, run)
    return best


def test_no_six_day_run_in_feasible_solution() -> None:
    days = month_days(2026, 7)
    people = [
        PersonInput(1, Role.A), PersonInput(2, Role.A),
        PersonInput(3, Role.A), PersonInput(4, Role.A),
    ]
    out = _solve(people, days, flight_pairs={d: 2 for d in days})

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for p in people:
        assert _max_run(grid, p.user_id, days) <= 5


def test_carry_streak_forces_early_off() -> None:
    """§5.5: 4 days carried over → at most 1 more working day before an X."""
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.T, carry_streak=4)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    # An X must appear within the first (6 - 4) = 2 days.
    assert AttendanceCode.X in {grid[(1, days[0])], grid[(1, days[1])]}


def test_carry_streak_five_forces_day_one_off() -> None:
    days = month_days(2026, 7)
    people = [PersonInput(1, Role.T, carry_streak=5)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    assert grid[(1, days[0])] is AttendanceCode.X


def _max_off_run(grid, user_id, days) -> int:
    run = best = 0
    for d in days:
        run = run + 1 if grid[(user_id, d)] is AttendanceCode.X else 0
        best = max(best, run)
    return best


def test_no_more_than_five_consecutive_off_days() -> None:
    """Customer rule 2026-06-12: ordinary off-runs never exceed 5 days."""
    days = month_days(2026, 7)
    people = [
        PersonInput(1, Role.A), PersonInput(2, Role.A),
        PersonInput(3, Role.A), PersonInput(4, Role.A),
    ]
    out = _solve(people, days, flight_pairs={d: 1 for d in days})

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for p in people:
        assert _max_off_run(grid, p.user_id, days) <= 5


def test_annual_leave_block_exempt_from_off_chain() -> None:
    """A registered 7-day annual leave is allowed (>5 off) — no violation."""
    days = month_days(2026, 7)
    leave_days = {date(2026, 7, d): AttendanceCode.AL for d in range(10, 17)}
    people = [PersonInput(1, Role.T), PersonInput(2, Role.A)]
    out = SchedulerEngine().solve(
        SolverInput(
            year=2026, month=7, people=people, days=days,
            weeks=build_weeks(days), flight_pairs={d: 0 for d in days},
            approved_off={1: leave_days},
            long_leave_off={1: set(leave_days)},
            max_solve_seconds=10.0,
        )
    )
    assert out.feasible
    off_chain = [v for v in out.violations if v.rule == "max_consecutive_off"]
    assert not off_chain  # the 7-day annual block is exempt


def test_conflicting_rules_still_return_schedule_with_violations() -> None:
    """One fixed person vs daily demand: rules cannot all hold → Violations,
    but a complete schedule is still returned (decision #2)."""
    days = month_days(2026, 7)[:14]
    people = [PersonInput(1, Role.A)]
    out = _solve(people, days, flight_pairs={d: 2 for d in days})

    assert out.feasible
    assert len(out.assignments) == len(days)
    assert out.violations  # staffing and/or off-quota slack fired
