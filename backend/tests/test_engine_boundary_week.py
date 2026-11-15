"""Known next-flight coverage respects max-five work runs, never weekly debt."""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput, objective_boundary_week
from app.scheduler.calendar_utils import month_days

A, X = AttendanceCode.A, AttendanceCode.X
GROUP_A = (1, 2, 3, 4)
DEC, JAN = month_days(2026, 12), month_days(2027, 1)
FIRST_JAN = [date(2027, 1, d) for d in (1, 2, 3)]
LAST_WEEK_DEC = [date(2026, 12, d) for d in (28, 29, 30, 31)]


def _solve(inp: SolverInput):
    out = SchedulerEngine(num_workers=1).solve(inp)
    assert out.feasible
    return out, {(a.user_id, a.day): a.code for a in out.assignments}



def _penalty(inp: SolverInput, fixed: dict[tuple[int, date], AttendanceCode]) -> int:
    """The look-ahead's smallest value with the given cells fixed."""
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    for (uid, d, code), var in x.items():
        if (uid, d) in fixed:
            model.add(var == int(fixed[(uid, d)] is code))
    terms = objective_boundary_week.terms(model, x, inp, 1)
    model.minimize(sum(terms))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    assert solver.solve(model) == cp_model.OPTIMAL
    return int(solver.objective_value)


def _input(days: list[date], pairs: int, **kw) -> SolverInput:
    return SolverInput(
        year=days[0].year, month=days[0].month,
        people=[PersonInput(u, Role.A) for u in GROUP_A],
        days=days, flight_pairs={d: pairs for d in days}, **kw,
    )


def test_unknown_next_flights_do_not_create_weekly_debt_or_demand() -> None:
    inp = _input(DEC, 2)
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    assert objective_boundary_week.terms(model, x, inp, 3000) == []


def test_only_known_next_flights_protect_consecutive_work_boundary() -> None:
    inp = _input(DEC, 1, next_flight_pairs={JAN[0]: 2})
    # Everyone working the final five days must rest January 1: three needed
    # workers cannot be supplied. Resetting one run restores one cover slot.
    worked = {(u, d): A for u in GROUP_A for d in DEC[-5:]}
    assert _penalty(inp, worked) == 3
    assert _penalty(inp, {**worked, (1, DEC[-1]): X}) == 2


def test_one_day_in_last_week_creates_no_rest_debt() -> None:
    days = month_days(2026, 11)
    inp = _input(days, 2, next_flight_pairs={date(2026, 12, d): 2 for d in range(1, 7)})
    fixed = {(u, d): X if d == days[-2] else A for u in GROUP_A for d in days[-5:]}
    assert _penalty(inp, fixed) == 0


def test_sunday_month_end_still_protects_next_day_consecutive_work() -> None:
    days = month_days(2027, 2)
    inp = _input(days, 1, next_flight_pairs={date(2027, 3, 1): 1})
    fixed = {(u, d): A for u in GROUP_A for d in days[-5:]}
    assert _penalty(inp, fixed) == 2
