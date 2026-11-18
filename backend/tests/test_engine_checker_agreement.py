"""The engine and the post-edit re-check count every rule the same way.

Property-style: seeded random small instances (6–8 people, 14–28 days, carried
history, approved leave, flights). The engine solves each one; the checker
(``schedule_violation_checker.recheck``) then reads the persisted grid. Both
verdicts are compared per (rule, user):

* the checker reports nothing the solved engine did not report;
* on the solved grid and on randomly edited copies of it, the engine's own
  constraints evaluated on that fixed grid flag exactly what the checker flags.

Window instances (owner 2026-11-18): a full month plus the next month's days
up to the Sunday ending its last week, with the month's first days already
decided (carried cells, a foreign working code and a leave among them). The
checker reads the window as the persisted months do: the month's own days,
then the carry days as a carry-only month (``carry_only``), each with the
history before it.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

import pytest
from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput, carried, constraints
from app.scheduler.calendar_utils import month_days, trailing_work_streak, window_days
from app.scheduler.domain import Violation
from app.scheduler.role_codes import codes_for
from app.scheduler.slack_registry import SlackRegistry
from app.services.schedule_violation_checker import recheck

AL = AttendanceCode.AL

ENGINE_RULES = {
    "monthly_off_shortfall": "monthly_shortfall",
    "monthly_off_excess": "monthly_excess",
    "max_consecutive_working": "consecutive",
    "max_consecutive_working_carry": "consecutive",
    "max_consecutive_off": "off_chain",
    "flight_staffing": "staffing",
    "role_a_minimum_a_days": "min_a",
    "comp_day_shortfall": "comp",
    "comp_day_excess": "comp",
    "role_f_staffing": "f_staffing",
    "role_f_weekly_off_shortfall": "f_rest_short",
    "role_f_weekly_off_excess": "f_rest_over",
}

def _engine_keys(violations: list[Violation]) -> set[tuple[str, int | None]]:
    return {(ENGINE_RULES[v.rule], v.user_id) for v in violations}


def _checker_keys(warnings: list[Violation]) -> set[tuple[str, int | None]]:
    # The checker reports the engine's rule names (and user_id) directly.
    return _engine_keys(warnings)


def _instance(seed: int, *, full_month: bool = False) -> SolverInput:
    rng = random.Random(seed)
    year, month = rng.choice([(2027, 2), (2027, 3), (2027, 8), (2028, 1)])
    length = rng.choice([14, 21, 28])
    # Also a full 30/31-day month, so the whole month (no 7-day blocks since
    # owner 2026-11-10) is compared, the last days included.
    days = month_days(year, month) if full_month else month_days(year, month)[:length]
    first = days[0]

    roles = [Role.M, Role.T, Role.F] + [Role.A] * rng.randint(3, 5)
    people: list[PersonInput] = []
    previous_working: dict[int, dict[date, bool]] = {}
    approved: dict[int, dict[date, AttendanceCode]] = {}
    annual: dict[int, set[date]] = {}
    leave_days_a: set[date] = set()

    for uid, role in enumerate(roles, start=1):
        work_code = next(c for c in codes_for(role) if c.is_working)
        # The previous month's last six days, oldest first: mostly work, some
        # rest, sometimes leave or sick; a third end on an off tail (off-run
        # across the boundary) and some on a long working run (carry streak).
        prev_list = [
            rng.choices(
                [work_code, AttendanceCode.X, AttendanceCode.CD, AL, AttendanceCode.S],
                weights=[6, 3, 1, 1, 1],
            )[0]
            for _ in range(6)
        ]
        tail = rng.random()
        if tail < 0.35:
            k = rng.randint(3, 5)
            prev_list[-k:] = [
                rng.choice([AttendanceCode.X, AttendanceCode.CD, AttendanceCode.S])
                for _ in range(k)
            ]
        elif tail < 0.55:
            k = rng.randint(4, 6)
            prev_list[-k:] = [work_code] * k
        # Like build_boundary_states: a day with no cell cuts prev_codes short
        # and counts as not worked in the weekly-rest flags.
        if rng.random() < 0.2:
            prev_list = prev_list[-rng.randint(1, 5) :]
        prev = tuple(prev_list)
        prev_days = [first - timedelta(days=n) for n in range(6, 0, -1)]
        known = dict(zip(prev_days[len(prev_days) - len(prev) :], prev, strict=True))
        previous_working[uid] = {
            d: d in known and known[d].is_working for d in prev_days
        }
        people.append(
            PersonInput(
                user_id=uid,
                role=role,
                carry_comp=rng.choice([0, 0, 1]),
                carry_streak=trailing_work_streak([c.is_working for c in prev]),
                carry_premium_off=rng.randint(0, 3),
                prev_codes=prev,
            )
        )

        # Approved leave for about half the people; at most one role-A person
        # off on any day so flight cover stays possible.
        if rng.random() < 0.5:
            length = rng.choice([2, 3, 5, 6, 7])
            start = rng.randrange(0, len(days) - length + 1)
            span = days[start : start + length]
            if role is Role.A and leave_days_a & set(span):
                continue
            if role is Role.A:
                leave_days_a |= set(span)
            approved[uid] = {d: AL for d in span}
            if length >= 6:
                annual[uid] = set(span)

    return SolverInput(
        year=year,
        month=month,
        people=people,
        days=days,
        flight_pairs={d: rng.choice([0, 1, 1, 2]) for d in days},
        approved_off=approved,
        holidays={rng.choice(days)},
        long_leave_off=annual,
        previous_working=previous_working,
        max_solve_seconds=3,
    )


def _fixed_grid_violations(
    inp: SolverInput, grid: dict[tuple[int, date], AttendanceCode]
) -> list[Violation]:
    """Engine constraints evaluated on a fixed decision-layer grid."""
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


def _checker_warnings(
    inp: SolverInput, grid: dict[tuple[int, date], AttendanceCode]
) -> list[str]:
    """The re-check over the persisted grid (pinned cells carry AL)."""
    persisted = {
        (uid, day): inp.approved_off.get(uid, {}).get(day, code)
        for (uid, day), code in grid.items()
    }
    return recheck(
        grid=persisted,
        roles={p.user_id: p.role for p in inp.people},
        carry_streaks={p.user_id: p.carry_streak for p in inp.people},
        days=inp.days,
        flight_pairs=inp.flight_pairs,
        previous_working=inp.previous_working,
        carry_comps={p.user_id: p.carry_comp for p in inp.people},
        annual_off=inp.long_leave_off,
        approved_off=inp.approved_off,
        prev_codes={p.user_id: p.prev_codes for p in inp.people},
    )


def _edited(
    inp: SolverInput, grid: dict[tuple[int, date], AttendanceCode], rng: random.Random
) -> dict[tuple[int, date], AttendanceCode]:
    """Random admin-style edits inside each person's code domain: single
    cells, a run of off days and a run of working days (often at the month
    start, against the carried history). Pinned leave cells stay pinned. No
    CD for a person who owes none: the engine forbids that outright (a hard
    rule, not a reported violation)."""
    out = dict(grid)
    people = {p.user_id: p for p in inp.people}
    days = sorted(inp.days)

    ahead = set(carried.ahead_days(inp))

    def choices(uid: int, *, working: bool | None = None) -> list[AttendanceCode]:
        person = people[uid]
        return [
            c
            for c in codes_for(person.role)
            if (c is not AttendanceCode.CD or person.carry_comp > 0)
            and (working is None or c.is_working == working)
        ]

    def set_cell(uid: int, day: date, code: AttendanceCode) -> None:
        # Carried cells are facts; no CD on the carry days (a hard rule).
        if code is AttendanceCode.CD and day in ahead:
            return
        if day not in inp.approved_off.get(uid, {}) and day not in inp.fixed.get(uid, {}):
            out[(uid, day)] = code

    for uid, day in rng.sample(sorted(out), k=8):
        set_cell(uid, day, rng.choice(choices(uid)))
    for working in (False, True):
        uid = rng.choice(sorted(people))
        length = rng.randint(4, 8)
        start = 0 if rng.random() < 0.4 else rng.randrange(0, len(days) - length + 1)
        for day in days[start : start + length]:
            set_cell(uid, day, rng.choice(choices(uid, working=working)))
    # Sometimes a role-A person loses every pure A day (D instead).
    role_a = sorted(uid for uid, p in people.items() if p.role is Role.A)
    if rng.random() < 0.3:
        uid = rng.choice(role_a)
        for day in days:
            if out[(uid, day)] is AttendanceCode.A:
                set_cell(uid, day, AttendanceCode.D)
    return out


@pytest.mark.parametrize(
    ("seed", "full_month"), [(11, False), (22, False), (33, False), (44, True)]
)
def test_engine_clean_grid_passes_checker(seed: int, full_month: bool) -> None:
    inp = _instance(seed, full_month=full_month)
    out = SchedulerEngine(num_workers=1).solve(inp)
    assert out.feasible
    grid = {(a.user_id, a.day): a.code for a in out.assignments}

    checker = _checker_keys(_checker_warnings(inp, grid))
    # The checker reports nothing the engine did not report.
    assert checker <= _engine_keys(out.violations)
    # On the same fixed grid the two verdicts are identical.
    assert _engine_keys(_fixed_grid_violations(inp, grid)) == checker

    # Edited grids break rules; engine and checker flag the same ones.
    rng = random.Random(seed)
    for _ in range(6):
        edited = _edited(inp, grid, rng)
        assert _engine_keys(_fixed_grid_violations(inp, edited)) == _checker_keys(
            _checker_warnings(inp, edited)
        )


# --- window instances (owner 2026-11-18) ------------------------------------


def _window_instance(seed: int) -> SolverInput:
    """A full month and its carry days; the month's first three days are
    carried cells (one person holds A/D, one T, one AL among them)."""
    base = _instance(seed, full_month=True)
    days = window_days(base.year, base.month)
    rng = random.Random(seed)
    roles = {p.user_id: p.role for p in base.people}
    stored: dict[int, dict[date, AttendanceCode]] = {}
    for uid, role in roles.items():
        work = next(c for c in codes_for(role) if c.is_working)
        stored[uid] = {d: rng.choice([work, work, AttendanceCode.X]) for d in days[:3]}
    role_a = sorted(uid for uid, role in roles.items() if role is Role.A)
    stored[role_a[0]][days[0]] = AttendanceCode.A_D
    stored[role_a[1]][days[1]] = AttendanceCode.T
    flexible = next(uid for uid, role in roles.items() if role is Role.T)
    stored[flexible][days[2]] = AL
    fixed, leave = carried.split(stored, roles)
    approved = {uid: dict(by_day) for uid, by_day in base.approved_off.items()}
    for uid, by_day in stored.items():
        for d in by_day:
            approved.get(uid, {}).pop(d, None)
    for uid, by_day in leave.items():
        approved.setdefault(uid, {}).update(by_day)
    for d in days[len(base.days) :]:
        base.flight_pairs[d] = rng.choice([1, 2])
    return SolverInput(
        year=base.year,
        month=base.month,
        people=base.people,
        days=days,
        flight_pairs=base.flight_pairs,
        approved_off=approved,
        holidays=base.holidays,
        long_leave_off=base.long_leave_off,
        previous_working=base.previous_working,
        fixed=fixed,
        max_solve_seconds=5,
    )


def _persisted(
    inp: SolverInput, grid: dict[tuple[int, date], AttendanceCode]
) -> dict[tuple[int, date], AttendanceCode]:
    """Stored codes: leave as AL, a carried cell as it was stored."""
    return {
        (uid, day): inp.approved_off.get(uid, {}).get(day)
        or inp.fixed.get(uid, {}).get(day)
        or code
        for (uid, day), code in grid.items()
    }


def _window_checker_warnings(
    inp: SolverInput, grid: dict[tuple[int, date], AttendanceCode]
) -> list[Violation]:
    """The month re-checked as persisted, then its carry days as the
    carry-only next month, whose history is the month's last days."""
    stored = _persisted(inp, grid)
    own, ahead = carried.own_days(inp), carried.ahead_days(inp)
    roles = {p.user_id: p.role for p in inp.people}
    month = recheck(
        grid={k: v for k, v in stored.items() if k[1] in set(own)},
        roles=roles,
        carry_streaks={p.user_id: p.carry_streak for p in inp.people},
        days=own,
        flight_pairs=inp.flight_pairs,
        carry_comps={p.user_id: p.carry_comp for p in inp.people},
        annual_off=inp.long_leave_off,
        approved_off=inp.approved_off,
        prev_codes={p.user_id: p.prev_codes for p in inp.people},
    )
    tail_prev = {uid: tuple(stored[(uid, d)] for d in own[-6:]) for uid in roles}
    tail = recheck(
        grid={k: v for k, v in stored.items() if k[1] in set(ahead)},
        roles=roles,
        carry_streaks={
            uid: trailing_work_streak([stored[(uid, d)].is_working for d in own])
            for uid in roles
        },
        days=ahead,
        flight_pairs=inp.flight_pairs,
        annual_off=inp.long_leave_off,
        approved_off=inp.approved_off,
        prev_codes=tail_prev,
        carry_only=True,
    )
    return month + tail


@pytest.mark.parametrize("seed", [50, 51, 52])
def test_engine_and_checker_agree_over_the_window(seed: int) -> None:
    inp = _window_instance(seed)
    assert carried.ahead_days(inp), "the instance must reach into the next month"
    out = SchedulerEngine(num_workers=1).solve(inp)
    assert out.feasible
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    # Carried cells are kept: in-domain codes as stored, foreign work as work.
    for uid, by_day in inp.fixed.items():
        for day, code in by_day.items():
            assert grid[(uid, day)].is_working == code.is_working
            if code in codes_for(next(p.role for p in inp.people if p.user_id == uid)):
                assert grid[(uid, day)] is code
    # No CD on the carry days.
    assert not any(
        code is AttendanceCode.CD and day in set(carried.ahead_days(inp))
        and day not in inp.approved_off.get(uid, {})
        for (uid, day), code in grid.items()
    )

    checker = _checker_keys(_window_checker_warnings(inp, grid))
    assert checker <= _engine_keys(out.violations)
    assert _engine_keys(_fixed_grid_violations(inp, grid)) == checker

    rng = random.Random(seed)
    for _ in range(6):
        edited = _edited(inp, grid, rng)
        assert _engine_keys(_fixed_grid_violations(inp, edited)) == _checker_keys(
            _window_checker_warnings(inp, edited)
        )
