"""Rest rules, preferred day-off pairs, fair turns (owner 2026-11-10 / 11-12).

The 7-day blocks (1–7, 8–14, …) are gone (2026-11-10), and so is the rolling
"any 7 consecutive days" reading (2026-11-12): the rest rules are at most 5
working days per Mon–Sun week (2 rest days, not necessarily adjacent) and
max-5-in-a-row; the soft objectives give every person as many
X as the month has Saturdays and Sundays (minus their approved leave on those
days), put the days off in pairs (Fri+Sat > Sat+Sun > Sun+Mon), keep a role
group from being all off on one day and share the good pairs in the group.
Acceptance items of the plan
``docs/superpowers/plans/2026-11-10-rest-rules-rolling-and-preferred-pairs.md``
are named in each test.

Tests assert properties of the optimum on small inputs the solver proves
optimal within the limit, so the default worker count is fine; none compares
two plans.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import month_days
from tests.rest_invariants import assert_rest_rules

X = AttendanceCode.X
FRI, SAT, SUN = 4, 5, 6
REST_RULES = {
    "weekly_max_five_working",
    "max_consecutive_working",
    "max_consecutive_working_carry",
}


def _solve(people, days, flight_pairs=None, seconds=30.0, **kw):
    return SchedulerEngine().solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
            flight_pairs=flight_pairs or {d: 0 for d in days},
            max_solve_seconds=seconds,
            **kw,
        )
    )


def _grid(out):
    return {(a.user_id, a.day): a.code for a in out.assignments}


def _offs(grid, uid, days) -> list[date]:
    return [d for d in days if grid[(uid, d)] is X]


def _pair_starts(grid, uid, days) -> list[date]:
    offs = set(_offs(grid, uid, days))
    return [d for d in sorted(offs) if d + timedelta(days=1) in offs]


# --- 1. the owner's November shape ------------------------------------------


def test_november_shape_staffed_without_rest_breaches() -> None:
    """4 group-A people, 21 two-pair days and 9 one-pair days, 3 F, 2 M:
    fewer flight_staffing violations than the block model's 3, no rest-rule
    violation, nobody works 6 days in a row."""
    days = month_days(2026, 11)
    one_pair = {2, 5, 9, 12, 16, 19, 23, 26, 30}
    fp = {d: (1 if d.day in one_pair else 2) for d in days}
    assert sum(1 for v in fp.values() if v == 2) == 21
    people = (
        [PersonInput(u, Role.A) for u in (1, 2, 3, 4)]
        + [PersonInput(u, Role.F) for u in (5, 6, 7)]
        + [PersonInput(u, Role.M) for u in (8, 9)]
    )
    out = _solve(people, days, fp, seconds=60.0)

    assert out.feasible
    rules = [v.rule for v in out.violations]
    assert rules.count("flight_staffing") < 3, rules
    assert not REST_RULES & set(rules), rules
    grid = _grid(out)
    for p in people:
        assert_rest_rules(grid, p.user_id, days)
    # Everyone gets the month's 9 Saturdays + Sundays as X — F and M no
    # longer get free days off (a probe with no target gave them 14–21).
    for p in people:
        assert len(_offs(grid, p.user_id, days)) == 9, (p.user_id, _offs(grid, p.user_id, days))


# --- 2/5/6. pairs, group cover, no free days off ----------------------------


@pytest.fixture(scope="module")
def f_and_m():
    """3 F + 2 M in November 2026, no flights (no staffing pressure)."""
    days = month_days(2026, 11)
    people = [PersonInput(u, Role.F) for u in (5, 6, 7)] + [
        PersonInput(u, Role.M) for u in (8, 9)
    ]
    out = _solve(people, days)
    assert out.feasible and not out.violations
    return days, people, _grid(out)


def test_days_off_come_in_pairs() -> None:
    """Acceptance 2: no isolated single X without staffing pressure (one
    person per role, so no group cover either)."""
    days = month_days(2026, 11)
    people = [PersonInput(1, Role.T), PersonInput(2, Role.F), PersonInput(3, Role.M)]
    out = _solve(people, days)
    assert out.feasible and not out.violations
    grid = _grid(out)
    for p in people:
        offs = set(_offs(grid, p.user_id, days))
        lonely = [
            d for d in sorted(offs)
            if d - timedelta(days=1) not in offs and d + timedelta(days=1) not in offs
        ]
        assert lonely == [], (p.user_id, lonely)


def test_role_group_is_never_all_off(f_and_m) -> None:
    """Acceptance 5: the 2 M and the 3 F are never all off on one day."""
    days, _people, grid = f_and_m
    for group in ((5, 6, 7), (8, 9)):
        for d in days:
            assert not all(grid[(u, d)] is X for u in group), (group, d)


def test_november_target_is_nine_for_f_and_m(f_and_m) -> None:
    """Acceptance 6: November 2026 has 9 Saturdays + Sundays → 9 X each."""
    days, people, grid = f_and_m
    for p in people:
        assert_rest_rules(grid, p.user_id, days)
        assert len(_offs(grid, p.user_id, days)) == 9, p.user_id


def test_july_target_is_eight_for_every_role() -> None:
    """Acceptance 6: July 2026 (the owner's paper roster) has 8 Saturdays +
    Sundays → 8 X for A, F, T and M alike."""
    days = month_days(2026, 7)
    people = (
        [PersonInput(u, Role.A) for u in (1, 2, 3, 4)]
        + [PersonInput(5, Role.F), PersonInput(6, Role.T)]
        + [PersonInput(u, Role.M) for u in (7, 8)]
    )
    out = _solve(people, days, {d: 1 for d in days}, seconds=60.0)
    assert out.feasible and not out.violations
    grid = _grid(out)
    for p in people:
        assert_rest_rules(grid, p.user_id, days)
        assert len(_offs(grid, p.user_id, days)) == 8, p.user_id


def test_leave_over_a_weekend_lowers_the_target_by_two() -> None:
    """Acceptance 6: leave Thu 12 – Mon 16 Nov 2026 (3 weekdays + the
    weekend between) → 9 − 2 = 7 chosen X; a colleague keeps 9."""
    days = month_days(2026, 11)
    leave = {date(2026, 11, d): AttendanceCode.AL for d in range(12, 17)}
    out = _solve(
        [PersonInput(1, Role.T), PersonInput(2, Role.T)], days, approved_off={1: leave}
    )
    assert out.feasible and not out.violations
    grid = _grid(out)
    chosen = [d for d in _offs(grid, 1, days) if d not in leave]
    assert len(chosen) == 7, chosen
    assert len(_offs(grid, 2, days)) == 9


# --- 3. preference order ----------------------------------------------------


def test_lone_person_gets_fri_sat_every_week() -> None:
    """Acceptance 3a: November 2026 starts on a Sunday, so Fri+Sat (6/7,
    13/14, 20/21, 27/28) fits the rest rules; the 9th X (9 Sat + Sun) joins
    one of the pairs."""
    days = month_days(2026, 11)
    out = _solve([PersonInput(1, Role.T)], days)
    assert out.feasible and not out.violations
    starts = _pair_starts(_grid(out), 1, days)
    assert {6, 13, 20, 27} <= {d.day for d in starts}
    assert {d.weekday() for d in starts} <= {FRI, SAT}


def test_sat_sun_when_friday_is_worked() -> None:
    """Acceptance 3b: a lone group-A person must work every Friday (a flight
    pair there), so Fri+Sat is impossible → Sat+Sun every week (Feb 2027
    starts on a Monday, so Sat+Sun fits the rest rules)."""
    days = month_days(2027, 2)
    fp = {d: (1 if d.weekday() == FRI else 0) for d in days}
    out = _solve([PersonInput(1, Role.A)], days, fp)
    assert out.feasible
    assert {v.rule for v in out.violations} == {"flight_staffing"}  # 1 person, 1A+1D
    grid = _grid(out)
    assert all(grid[(1, d)].is_working for d in days if d.weekday() == FRI)
    starts = _pair_starts(grid, 1, days)
    assert [d.day for d in starts] == [6, 13, 20, 27]
    assert {d.weekday() for d in starts} == {SAT}


def test_sun_mon_when_friday_and_saturday_are_worked() -> None:
    """Acceptance 3c: flights on Friday and Saturday → Sun+Mon every week
    (June 2027 starts on a Tuesday, so Sun+Mon fits the rest rules)."""
    days = month_days(2027, 6)
    fp = {d: (1 if d.weekday() in (FRI, SAT) else 0) for d in days}
    out = _solve([PersonInput(1, Role.A)], days, fp)
    assert out.feasible
    starts = _pair_starts(_grid(out), 1, days)
    assert [d.day for d in starts] == [6, 13, 20, 27]
    assert {d.weekday() for d in starts} == {SUN}


# --- 4. fair turns ----------------------------------------------------------


def test_good_pairs_are_shared_in_a_group() -> None:
    """Acceptance 4: three
    T over February 2027 with group cover on — never all off, everybody gets
    a weekday-bonus pair, and nobody gets a day off beyond the target (8)
    to make it happen."""
    days = month_days(2027, 2)
    people = [PersonInput(u, Role.T) for u in (1, 2, 3)]
    out = _solve(people, days)
    assert out.feasible and not out.violations
    grid = _grid(out)
    for d in days:
        assert not all(grid[(u, d)] is X for u in (1, 2, 3)), d
    for u in (1, 2, 3):
        assert len(_offs(grid, u, days)) == 8
        starts = _pair_starts(grid, u, days)
        assert {d.weekday() for d in starts} & {FRI, SAT, SUN}, (u, starts)


# --- 7. month boundary ------------------------------------------------------


def test_history_closes_the_week_across_the_month_start() -> None:
    """Acceptance 7: Sun 1 Nov 2026 closes the week Mon 26 – Sun 1 whose
    27–31 Oct were worked (history) → the 1st is a rest day (rule W, and
    rule C allows one more day at most); without history the month may
    open with 5 working days."""
    days = month_days(2026, 11)
    first = days[0]
    worked = {first - timedelta(days=n): n <= 5 for n in range(1, 7)}
    out = _solve(
        [PersonInput(1, Role.T, carry_streak=5)], days, previous_working={1: worked}
    )
    assert out.feasible and not out.violations
    grid = _grid(out)
    assert not grid[(1, days[0])].is_working
    assert_rest_rules(grid, 1, days, worked, carry_streak=5)

    out = _solve([PersonInput(1, Role.T)], days)
    grid = _grid(out)
    assert all(grid[(1, d)].is_working for d in days[:5])


def test_pair_may_start_on_last_months_last_day() -> None:
    """An X on Sat 31 Oct (history) + X on Sun 1 Nov is a Sat+Sun pair with
    its bonus; after leave (AL) or a worked day there is no bonus pair."""
    from ortools.sat.python import cp_model

    from app.scheduler import objective_off_pairing

    days = month_days(2026, 11)

    def boundary_pairs(last_code):
        inp = SolverInput(
            year=2026, month=11, days=days, flight_pairs={},
            people=[PersonInput(1, Role.T, prev_codes=(last_code,))],
        )
        model = cp_model.CpModel()
        x = SchedulerEngine()._build_vars(model, inp)
        return [
            (p.first, p.bonus)
            for p in objective_off_pairing.bonus_pairs(model, x, inp)
            if p.first < days[0]
        ]

    assert boundary_pairs(X) == [(date(2026, 10, 31), 2)]
    assert boundary_pairs(AttendanceCode.AL) == []
    assert boundary_pairs(AttendanceCode.AD) == []
