"""Ordinary rest is capped at three consecutive days, including boundaries."""

from datetime import date

import pytest
from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode as C
from app.models.enums import Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput, constraints_off_chain
from app.scheduler.slack_registry import SlackRegistry
from app.services.schedule_violation_checker import check_off_chain


def _verdicts(codes, *, previous=(), approved=None, role=Role.T):
    days = [date(2027, 3, n) for n in range(1, len(codes) + 1)]
    approved = approved or {}
    inp = SolverInput(
        2027, 3, [PersonInput(1, role, prev_codes=previous)], days, {}, approved_off={1: approved}
    )
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    registry = SlackRegistry()
    constraints_off_chain.add(model, x, inp, registry)
    for (_uid, d, code), var in x.items():
        expected = C.X if d in approved else codes[d.day - 1]
        model.add(var == int(code is expected))
    model.minimize(sum(registry.penalty_terms()))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    assert solver.solve(model) == cp_model.OPTIMAL
    persisted = {(1, d): approved.get(d, codes[d.day - 1]) for d in days}
    engine = registry.violations(solver)
    checker = check_off_chain(persisted, {1: role}, days, {}, prev_codes={1: previous})
    assert [(v.rule, v.day) for v in engine] == [(v.rule, v.day) for v in checker]
    return engine


@pytest.mark.parametrize("role", list(Role))
def test_four_ordinary_rest_days_are_reported_for_every_role(role):
    violations = _verdicts([C.X] * 4, role=role)
    assert [(v.rule, v.day) for v in violations] == [("max_consecutive_off", date(2027, 3, 1))]


def test_three_ordinary_rest_days_are_allowed():
    assert _verdicts([C.X] * 3) == []


def test_two_plus_two_boundary_rest_is_reported():
    violations = _verdicts([C.X, C.X], previous=(C.X, C.X))
    assert [(v.rule, v.day) for v in violations] == [("max_consecutive_off", date(2027, 2, 27))]


def test_comp_days_count_towards_the_four_day_rest_limit():
    assert len(_verdicts([C.X, C.CD, C.X, C.CD])) == 1


def test_annual_leave_exception_is_preserved():
    assert _verdicts([C.X] * 4, approved={date(2027, 3, 2): C.AL}) == []
    assert _verdicts([C.X, C.X], previous=(C.AL, C.X)) == []


def test_approved_comp_day_does_not_exempt_four_day_rest_run():
    assert len(_verdicts([C.X] * 4, approved={date(2027, 3, 2): C.CD})) == 1
