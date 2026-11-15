"""Monthly entitlement replaces weekly quotas and agrees on persisted leave."""

from datetime import date

import pytest
from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode as C
from app.models.enums import Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput, constraints
from app.scheduler.calendar_utils import month_days
from app.scheduler.objective_monthly_off_target import target
from app.scheduler.slack_registry import SlackRegistry
from app.services.schedule_violation_checker import recheck


def verdicts(days, rest, *, approved=None, cd=(), carry=0, carry_comp=0):
    approved = approved or {}
    inp = SolverInput(
        days[0].year,
        days[0].month,
        [PersonInput(1, Role.T, carry_streak=carry, carry_comp=carry_comp)],
        days,
        {},
        approved_off={1: approved},
    )
    grid = {
        (1, d): C.X if d.day in rest or d in approved else C.CD if d.day in cd else C.AD
        for d in days
    }
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    registry = SlackRegistry()
    constraints.add_all(model, x, inp, registry)
    for (uid, d, code), var in x.items():
        model.add(var == int(grid[(uid, d)] is code))
    model.minimize(sum(registry.penalty_terms()))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    assert solver.solve(model) == cp_model.OPTIMAL
    engine = registry.violations(solver)
    persisted = {(u, d): approved.get(d, c) for (u, d), c in grid.items()}
    checker = recheck(
        persisted,
        {1: Role.T},
        {1: carry},
        days,
        {},
        carry_comps={1: carry_comp},
        approved_off={1: approved},
    )

    # Consecutive violations intentionally have carry-specific engine keys.
    def normalize(vs):
        return {(v.rule.replace("_carry", ""), v.user_id) for v in vs}

    assert normalize(engine) == normalize(checker)
    return engine, inp, persisted


def test_one_rest_week_and_three_rest_week_are_legal():
    days = month_days(2027, 3)
    # Week one has one X, week two three; total exactly eight X, max run five.
    violations, _, _ = verdicts(days, {4, 8, 11, 14, 18, 21, 25, 28})
    assert violations == []


@pytest.mark.parametrize(("year", "month"), [(2027, 2), (2028, 2), (2026, 11), (2027, 3)])
def test_exact_entitlement_for_all_month_lengths(year, month):
    days = month_days(year, month)
    weekends = {d.day for d in days if d.weekday() >= 5}
    violations, inp, _ = verdicts(days, weekends)
    assert violations == []
    assert len(days) - target(inp, 1) == sum(d.weekday() < 5 for d in days)
    weekday = next(d for d in days if d.weekday() < 5)
    violations, _, _ = verdicts(days, weekends | {weekday.day})
    monthly = [v for v in violations if v.rule.startswith("monthly_off")]
    assert [(v.rule, v.params) for v in monthly] == [
        ("monthly_off_excess", {"target": len(weekends), "amount": 1})
    ]


def test_shortfall_is_explicit_and_not_hidden_as_preference():
    days = month_days(2027, 3)
    violations, _, _ = verdicts(days, {4, 8, 11, 14, 18, 21, 25})
    assert any(v.rule == "monthly_off_shortfall" and v.params["amount"] == 1 for v in violations)


@pytest.mark.parametrize("leave_day", [3, 6])
def test_approved_leave_never_requires_makeup_work(leave_day):
    days = month_days(2027, 3)
    weekends = {d.day for d in days if d.weekday() >= 5}
    leave = {date(2027, 3, leave_day): C.AL}
    violations, inp, grid = verdicts(days, weekends, approved=leave)
    assert violations == []
    assert sum(c.is_working for c in grid.values()) == 23 - (leave_day == 3)
    assert sum(c is C.X for c in grid.values()) == target(inp, 1)


def test_comp_day_is_additional_to_ordinary_x_entitlement():
    days = month_days(2027, 3)
    weekends = {d.day for d in days if d.weekday() >= 5}
    violations, _, grid = verdicts(days, weekends, cd={3}, carry_comp=1)
    assert violations == []
    assert sum(c.is_working for c in grid.values()) == 22


def test_pinned_comp_day_is_counted_once_after_persistence():
    days = month_days(2027, 3)
    weekends = {d.day for d in days if d.weekday() >= 5}
    violations, _, _ = verdicts(days, weekends, approved={date(2027, 3, 3): C.CD}, carry_comp=1)
    assert violations == []


def test_boundary_five_plus_one_is_still_reported():
    days = month_days(2027, 3)
    violations, _, _ = verdicts(days, {4, 8, 11, 14, 18, 21, 25, 28}, carry=5)
    assert any(v.rule == "max_consecutive_working_carry" for v in violations)


def test_existing_x_inside_approved_span_remains_ordinary_rest():
    days = month_days(2027, 3)
    rest = {4, 8, 11, 14, 18, 21, 25, 28}
    grid = {(1, d): C.X if d.day in rest else C.AD for d in days}
    # Approval preserves an existing weekday X, while recording the whole
    # span. Only the persisted AL is leave; X must remain ordinary rest.
    approved = {date(2027, 3, 4): C.AL, date(2027, 3, 5): C.AL}
    grid[(1, date(2027, 3, 5))] = C.AL
    assert recheck(grid, {1: Role.T}, {}, days, {}, approved_off={1: approved}) == []
