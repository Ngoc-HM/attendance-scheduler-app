"""Boundary-week look-ahead for group A (``objective_boundary_week``).

Rule W caps only this month's part of a last week that runs into next month.
The look-ahead makes the month leave group A enough rest owed for next
month's first days to still be staffed — an objective, never a reported rule.
Solver tests that compare plans pin ``num_workers=1``.
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput, objective_boundary_week
from app.scheduler.calendar_utils import month_days, trailing_work_streak
from tests.rest_invariants import assert_rest_rules

A, X = AttendanceCode.A, AttendanceCode.X
GROUP_A = (1, 2, 3, 4)
DEC, JAN = month_days(2026, 12), month_days(2027, 1)
FIRST_JAN = [date(2027, 1, d) for d in (1, 2, 3)]
LAST_WEEK_DEC = [date(2026, 12, d) for d in (28, 29, 30, 31)]


def _solve(inp: SolverInput):
    out = SchedulerEngine(num_workers=1).solve(inp)
    assert out.feasible
    return out, {(a.user_id, a.day): a.code for a in out.assignments}


def test_december_leaves_january_a_startable_week() -> None:
    """December 2026 ends on a Thursday; one flight pair a day all December,
    two on Fri 1 – Sun 3 Jan (3 of the 4 group-A people at work, so only 3
    rest days fit there while the week of 28 Dec owes 4 x 2). December rests
    at least 5 of them in its last four days, so January (with December as
    history) staffs 1–3 January and breaks no week. (Two pairs on every day
    of that week could not work at all: 7 rest slots for 8 rests owed.)"""
    dec_fp = {d: 1 for d in DEC}
    people = [PersonInput(u, Role.A) for u in GROUP_A]
    out, dec = _solve(
        SolverInput(
            year=2026, month=12, people=people, days=DEC, flight_pairs=dec_fp,
            next_flight_pairs={d: 2 for d in FIRST_JAN}, max_solve_seconds=60.0,
        )
    )
    assert out.violations == []  # the look-ahead itself is never reported
    rested = {
        u: sum(1 for d in LAST_WEEK_DEC if not dec[(u, d)].is_working) for u in GROUP_A
    }
    print("December rests in 28–31 Dec:", rested,
          "X:", {u: sum(1 for d in DEC if dec[(u, d)] is X) for u in GROUP_A})
    assert sum(rested.values()) >= 8 - 3, rested

    tail = DEC[-6:]
    jan_people = [
        PersonInput(
            u, Role.A,
            carry_streak=trailing_work_streak([dec[(u, d)].is_working for d in tail]),
            prev_codes=tuple(dec[(u, d)] for d in tail),
        )
        for u in GROUP_A
    ]
    out, jan = _solve(
        SolverInput(
            year=2027, month=1, people=jan_people, days=JAN,
            flight_pairs={d: (2 if d in FIRST_JAN else 1) for d in JAN},
            previous_working={u: {d: dec[(u, d)].is_working for d in tail} for u in GROUP_A},
            max_solve_seconds=60.0,
        )
    )
    early = [
        (v.rule, v.day) for v in out.violations
        if v.rule in ("flight_staffing", "weekly_max_five_working")
        and v.day is not None and v.day <= FIRST_JAN[-1]
    ]
    assert early == [], early
    for u in GROUP_A:
        history = {d: dec[(u, d)].is_working for d in tail}
        assert_rest_rules(jan, u, JAN, history, carry_streak=jan_people[u - 1].carry_streak)


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


def test_month_ending_on_sunday_has_no_term() -> None:
    """February 2027 ends on Sunday 28: no week runs into March."""
    inp = _input(month_days(2027, 2), 2)
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    assert objective_boundary_week.terms(model, x, inp, 3000) == []


def test_one_day_in_the_last_week_forces_nothing() -> None:
    """November 2026 ends on Monday 30: everyone working that day owes 2
    rest days in 1–6 December, 8 in all; with one flight pair a day (from
    the last full week, no December data yet) those six days absorb 6 x 2 =
    12 — nothing to pay."""
    days = month_days(2026, 11)
    worked = {(u, days[-1]): A for u in GROUP_A}
    assert _penalty(_input(days, 1), worked) == 0


def test_shortfall_is_counted_from_next_months_flights() -> None:
    """Same day, but December's first six days are known to have two pairs:
    capacity 6 x 1 = 6 against 8 owed → 2 units; one person resting on the
    30th owes 1 less."""
    days = month_days(2026, 11)
    ahead = {date(2026, 12, d): 2 for d in range(1, 7)}
    inp = _input(days, 1, next_flight_pairs=ahead)
    worked = {(u, days[-1]): A for u in GROUP_A}
    assert _penalty(inp, worked) == 2
    assert _penalty(inp, {**worked, (1, days[-1]): X}) == 1
    # A day with no data falls back to the last full week (one pair here).
    assert _penalty(_input(days, 1, next_flight_pairs={days[-1] + timedelta(days=1): 2}),
                    worked) == 0

