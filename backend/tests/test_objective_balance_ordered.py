"""Monthly A/D fairness must protect every role-A person's rank."""

from datetime import date, timedelta

import pytest
from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler import objective_balance
from app.scheduler.domain import PersonInput, SolverInput
from app.scheduler.engine import SchedulerEngine


def _instance(n_people=4, n_days=12):
    days = [date(2026, 6, 1) + timedelta(days=i) for i in range(n_days)]
    return SolverInput(2026, 6, [PersonInput(i, Role.A) for i in range(n_people)], days, {})


def _solve_stages(model, stages):
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    for _, expr in stages:
        model.minimize(expr)
        assert solver.solve(model) == cp_model.OPTIMAL
        model.add(expr == solver.value(expr))
    return solver


@pytest.mark.parametrize(
    "unfair,fair",
    [
        ([12, 0, 0, 0], [3, 3, 3, 3]),
        ([4, 4, 4, 4, 2, 0], [4, 4, 4, 3, 3, 0]),
    ],
)
def test_fairness_rejects_concentration_including_after_third_rank(unfair, fair):
    inp = _instance(len(unfair))
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    choose_fair = model.new_bool_var("choose_fair")
    for person in inp.people:
        for i, day in enumerate(inp.days):
            for code in (AttendanceCode.A, AttendanceCode.D, AttendanceCode.X, AttendanceCode.CD):
                # Each alternative has the listed A count and no D duties.
                unfair_code = AttendanceCode.A if i < unfair[person.user_id] else AttendanceCode.X
                fair_code = AttendanceCode.A if i < fair[person.user_id] else AttendanceCode.X
                model.add(x[person.user_id, day, code] == int(code == fair_code)).only_enforce_if(
                    choose_fair
                )
                model.add(x[person.user_id, day, code] == int(code == unfair_code)).only_enforce_if(
                    choose_fair.Not()
                )
    stages = objective_balance.ordered_terms(model, x, inp)
    # A lower preference actively asks for the unfair alternative. In the
    # six-person fixture, aggregate gap and shift spread tie, so only rank 4
    # can protect the fair alternative from this preference.
    solver = _solve_stages(model, stages + [("prefer_unfair", choose_fair)])
    assert solver.value(choose_fair) == 1


@pytest.mark.parametrize("n_days,want", [(10, 0), (11, 1)])
def test_individual_balance_respects_even_and_odd_work_counts(n_days, want):
    inp = _instance(1, n_days)
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    for day in inp.days:
        model.add(x[0, day, AttendanceCode.A] + x[0, day, AttendanceCode.D] == 1)
    solver = _solve_stages(model, objective_balance.ordered_terms(model, x, inp))
    n_a = sum(solver.value(x[0, d, AttendanceCode.A]) for d in inp.days)
    n_d = sum(solver.value(x[0, d, AttendanceCode.D]) for d in inp.days)
    assert abs(n_a - n_d) == want


def test_d_heavy_demand_distributes_unavoidable_gap():
    inp = _instance(3, 3)
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    for day in inp.days:
        for person in inp.people:
            model.add(
                x[person.user_id, day, AttendanceCode.A] + x[person.user_id, day, AttendanceCode.D]
                == 1
            )
        model.add(sum(x[p.user_id, day, AttendanceCode.A] for p in inp.people) == 1)
    solver = _solve_stages(model, objective_balance.ordered_terms(model, x, inp))
    assert [
        sum(solver.value(x[p.user_id, d, AttendanceCode.A]) for d in inp.days) for p in inp.people
    ] == [1, 1, 1]
