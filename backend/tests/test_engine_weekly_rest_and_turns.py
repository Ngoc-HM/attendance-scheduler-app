"""Owner rulings of 2026-11-12: two rest rules, and good pairs in turns.

Rest rules (both soft with slack, reported when broken):

* W ``weekly_max_five_working``: at most 5 working days in every Mon–Sun
  calendar week — 2 rest days a week, NOT necessarily adjacent; weeks run
  across month boundaries (history before the 1st; the week ending next
  month caps only this month's days).
* C ``max_consecutive_working``: no more than 5 working days in a row; one
  rest day resets the run.

The rolling reading ("any 7 consecutive days", ``rolling_seven_min_two_rest``)
is gone: with the month's fixed number of X it forced the same two weekdays
every week. Single days off are a normal tool of the roster.

Good pairs (Fri+Sat 3, Sat+Sun 2, Sun+Mon 1) are taken in turns inside a
role group, with the memory of the 12 months before
(``PersonInput.carry_pair_points``, ``objective_pair_points_fair``).

Engine verdicts on a fixed grid use the engine's own constraints; solver
tests that compare plans pin ``num_workers=1``.
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.core.i18n import MESSAGES
from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput, constraints
from app.scheduler.calendar_utils import month_days
from app.scheduler.domain import Violation
from app.scheduler.slack_registry import SlackRegistry
from app.services.carry_over_math import pair_points
from app.services.schedule_violation_checker import recheck
from tests.rest_invariants import assert_rest_rules

X, AD = AttendanceCode.X, AttendanceCode.AD
FRI = 4
MARCH_2027 = month_days(2027, 3)  # starts on a Monday


def _input(people, days, **kw) -> SolverInput:
    return SolverInput(
        year=days[0].year,
        month=days[0].month,
        people=people,
        days=days,
        flight_pairs={d: 0 for d in days},
        max_solve_seconds=kw.pop("seconds", 30.0),
        **kw,
    )


def _grid(out) -> dict[tuple[int, date], AttendanceCode]:
    return {(a.user_id, a.day): a.code for a in out.assignments}


def _plan(days: list[date], rest: set[int]) -> dict[tuple[int, date], AttendanceCode]:
    """User 1 rests on the given days of the month, works the others."""
    return {(1, d): (X if d.day in rest else AD) for d in days}


def _engine_on_grid(inp: SolverInput, grid) -> set[tuple[str, date | None]]:
    """The engine's rules evaluated on a fixed grid (as the agreement test)."""
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
    return _keys(registry.violations(solver))


def _checker(inp: SolverInput, grid) -> set[tuple[str, date | None]]:
    return _keys(
        recheck(
            grid=grid,
            roles={p.user_id: p.role for p in inp.people},
            carry_streaks={p.user_id: p.carry_streak for p in inp.people},
            days=inp.days,
            flight_pairs=inp.flight_pairs,
            previous_working=inp.previous_working,
        )
    )


def _keys(violations: list[Violation]) -> set[tuple[str, date | None]]:
    return {(v.rule, v.day) for v in violations}


def _both(inp: SolverInput, grid) -> set[tuple[str, date | None]]:
    engine, checker = _engine_on_grid(inp, grid), _checker(inp, grid)
    assert engine == checker, (engine, checker)
    return engine


# --- rule W and rule C on fixed grids ---------------------------------------


def test_rest_days_need_not_be_adjacent() -> None:
    """Legal: rest Mon 1 + Tue 2, work Wed 3 – Sun 7, rest Mon 8, work Tue 9 –
    Sat 13, rest Sun 14, … — one rolling 7-day window (Wed 3 – Tue 9) holds 6
    working days, yet every week has 2 rest days and no run exceeds 5. Two
    single rest days in a week (Mon + Sun) are fine too."""
    inp = _input([PersonInput(1, Role.T)], MARCH_2027)
    grid = _plan(MARCH_2027, {1, 2, 8, 14, 15, 21, 22, 28, 29})
    window = [date(2027, 3, d) for d in range(3, 10)]
    assert sum(grid[(1, d)].is_working for d in window) == 6
    assert _both(inp, grid) == set()


def test_good_pairs_can_move_through_the_week() -> None:
    """Fri+Sat → Wed+Thu → Mon+Tue → Mon & Sun (two singles) → … over four
    weeks: exactly 2 rest days a week, never more than 5 in a row — legal."""
    inp = _input([PersonInput(1, Role.T)], MARCH_2027)
    grid = _plan(MARCH_2027, {5, 6, 10, 11, 15, 16, 22, 28, 29, 30})
    assert _both(inp, grid) == set()


def test_week_with_six_working_days_is_reported() -> None:
    """Rest only on Thu 4 in the week of 1 March (Mon–Wed, Fri–Sun worked, no
    run longer than 3): rule W alone is reported, by engine and re-check."""
    inp = _input([PersonInput(1, Role.T)], MARCH_2027)
    rest = {4, 8, 11, 14, 18, 21, 25, 28}  # later weeks: 2 single rest days
    assert _both(inp, _plan(MARCH_2027, rest)) == {
        ("weekly_max_five_working", date(2027, 3, 1))
    }


def test_six_in_a_row_is_still_reported() -> None:
    """Rule C stays: 6 working days in a row across two weeks (Wed 3 – Mon 8,
    each week with 2 rest days) is reported as ``max_consecutive_working``."""
    inp = _input([PersonInput(1, Role.T)], MARCH_2027)
    grid = _plan(MARCH_2027, {1, 2, 9, 14, 15, 21, 22, 28, 29})
    assert _both(inp, grid) == {("max_consecutive_working", date(2027, 3, 3))}


def test_week_across_the_month_start_uses_history() -> None:
    """November 2026 starts on Sunday: the week Mon 26 Oct – Sun 1 Nov.
    Without history Sun 1 can be worked; with Mon 26 – Fri 30 Oct worked
    (Sat 31 off, so no run is carried) it is the week's 6th working day; a
    day with no history counts as not worked."""
    days = month_days(2026, 11)
    rest = {2, 8, 9, 15, 16, 22, 23, 29, 30}
    grid = _plan(days, rest)
    worked = {date(2026, 10, d): d <= 30 for d in range(26, 32)}
    plain = _input([PersonInput(1, Role.T)], days)
    assert _both(plain, grid) == set()
    partial = _input(
        [PersonInput(1, Role.T)], days,
        previous_working={1: {d: v for d, v in worked.items() if d.day >= 27}},
    )
    assert _both(partial, grid) == set()
    with_history = _input([PersonInput(1, Role.T)], days, previous_working={1: worked})
    assert _both(with_history, grid) == {("weekly_max_five_working", date(2026, 10, 26))}


def test_last_partial_week_caps_only_the_days_of_this_month() -> None:
    """October 2026 ends on Saturday: Mon 26 – Fri 30 worked, Sat 31 off is
    fine (Sunday belongs to November); all six worked is reported."""
    days = month_days(2026, 10)
    inp = _input([PersonInput(1, Role.T)], days)
    rest = {3, 4, 10, 11, 17, 18, 24, 25}
    assert _both(inp, _plan(days, rest | {31})) == set()
    assert ("weekly_max_five_working", date(2026, 10, 26)) in _both(inp, _plan(days, rest))


def test_solver_keeps_both_rules_and_the_old_rule_is_gone() -> None:
    """The solver: 6 worked days before the month (Mon 26 – Sat 31 Oct)
    already break the week of 26 Oct whatever Sun 1 holds — reported once,
    with that Monday; the rest of the plan follows both rules. No text key
    for the rolling rule remains."""
    days = month_days(2026, 11)
    worked = {date(2026, 10, d): True for d in range(26, 32)}
    out = SchedulerEngine(num_workers=1).solve(
        _input([PersonInput(1, Role.T, carry_streak=6)], days, previous_working={1: worked})
    )
    assert out.feasible
    rules = {(v.rule, v.day) for v in out.violations}
    assert ("weekly_max_five_working", date(2026, 10, 26)) in rules
    assert {r for r, _ in rules} <= {"weekly_max_five_working", "max_consecutive_working_carry"}
    grid = _grid(out)
    assert grid[(1, days[0])] is X
    assert_rest_rules(grid, 1, days[1:])
    for lang in MESSAGES.values():
        assert "schedule.violation.rolling_seven_min_two_rest" not in lang
        assert "schedule.violation.weekly_max_five_working" in lang


# --- good pairs in turns, with memory ---------------------------------------

FEB_2027 = month_days(2027, 2)  # Mon 1 – Sun 28: 4 full weeks, target 8


def _points(grid, uid: int) -> int:
    return pair_points(d for d in FEB_2027 if grid[(uid, d)] is X)


def _fri_sat(grid, uid: int) -> int:
    offs = {d for d in FEB_2027 if grid[(uid, d)] is X}
    return sum(1 for d in offs if d.weekday() == FRI and d + timedelta(days=1) in offs)


def _solve_group(carries: tuple[int, ...]):
    people = [
        PersonInput(uid, Role.T, carry_pair_points=c)
        for uid, c in enumerate(carries, start=1)
    ]
    out = SchedulerEngine(num_workers=1).solve(_input(people, FEB_2027, seconds=60.0))
    assert out.feasible and out.violations == []
    grid = _grid(out)
    for p in people:
        assert_rest_rules(grid, p.user_id, FEB_2027)
        assert sum(1 for d in FEB_2027 if grid[(p.user_id, d)] is X) == 8
    return grid


def test_turns_inside_a_month() -> None:
    """3 T, no staffing floor, February 2027 (4 weeks), equal history: every
    member gets a Fri+Sat pair and the bonus points differ by at most one
    pair's worth (3)."""
    grid = _solve_group((0, 0, 0))
    points = [_points(grid, u) for u in (1, 2, 3)]
    fri_sat = [_fri_sat(grid, u) for u in (1, 2, 3)]
    print("turns inside a month: Fri+Sat", fri_sat, "points", points)
    assert min(fri_sat) >= 1, (fri_sat, points)
    assert max(points) - min(points) <= 3, (fri_sat, points)


def test_turns_with_memory() -> None:
    """Same group, member 1 carrying 12 points more than the others: member
    1 yields — the fewest bonus points this month."""
    grid = _solve_group((12, 0, 0))
    points = {u: _points(grid, u) for u in (1, 2, 3)}
    print("turns with memory: points", points, "Fri+Sat", {u: _fri_sat(grid, u) for u in points})
    assert points[1] < min(points[2], points[3]), points


def test_the_leader_yields_to_the_middle_when_the_lowest_is_capped() -> None:
    """Live run of December 2026 (3 F): the lowest member cannot earn more
    than one pair, so the reward on the minimum is spent — the four pairs
    left must still go to the one behind (carry 4) before the leader (carry
    6), even when another soft term (here 10 per point) pulls for the
    leader. Model of the objective alone, no roster."""
    from app.scheduler import objective_pair_points_fair
    from app.scheduler.objective_off_pairing import BonusPair

    people = [PersonInput(uid, Role.T, carry_pair_points=c) for uid, c in ((1, 0), (2, 4), (3, 6))]
    model = cp_model.CpModel()
    day = MARCH_2027[4]
    own = BonusPair(1, day, model.new_bool_var("own"), 3)
    slots = [
        (BonusPair(2, day, model.new_bool_var(f"mid{n}"), 3),
         BonusPair(3, day, model.new_bool_var(f"top{n}"), 3))
        for n in range(4)
    ]
    for mid, top in slots:
        model.add(mid.var + top.var <= 1)  # one pair, one taker
    found = [own] + [pair for slot in slots for pair in slot]
    terms = objective_pair_points_fair.terms(
        model, found, _input(people, MARCH_2027), weight=60, spread_weight=5
    )
    pull = sum(10 * 3 * top.var for _, top in slots)
    model.minimize(sum(terms) - sum(15 * p.bonus * p.var for p in found) - pull)
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    assert solver.solve(model) == cp_model.OPTIMAL
    taken = (sum(solver.value(mid.var) for mid, _ in slots),
             sum(solver.value(top.var) for _, top in slots))
    assert solver.value(own.var) == 1
    assert taken == (2, 2), taken  # running totals 3 / 10 / 12, not 3 / 4 / 18
