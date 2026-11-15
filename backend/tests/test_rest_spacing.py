"""Ordinary rest is spread in pairs; triples are a last resort."""

import time
from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode as C
from app.models.enums import Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput, objectives
from app.scheduler.calendar_utils import month_days
from app.scheduler.optimization import solve_ordered


def test_two_pairs_preferred_to_a_triple_and_single_day():
    days = month_days(2027, 2)[:8]
    inp = SolverInput(2027, 2, [PersonInput(1, Role.A)], days, {})
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    triple = model.new_bool_var("choose_triple")
    for (_, d, code), var in x.items():
        pair_code = C.X if d.day in {1, 2, 5, 6} else C.A
        triple_code = C.X if d.day in {1, 5, 6, 7} else C.A
        model.add(var == int(code is pair_code)).only_enforce_if(triple.Not())
        model.add(var == int(code is triple_code)).only_enforce_if(triple)
    stages = objectives.ordered_terms(model, x, inp)
    # A very attractive lower preference cannot buy an unnecessary triple.
    stages.append(("prefer_triple", -1000000 * triple))

    def factory(seconds):
        solver = cp_model.CpSolver()
        solver.parameters.num_workers = 1
        solver.parameters.max_time_in_seconds = seconds
        return solver

    result = solve_ordered(model, stages, deadline=time.monotonic() + 5, solver_factory=factory)
    assert result.solver.value(triple) == 0


def test_spacing_stage_precedes_shift_and_weekday_preferences():
    days = [date(2027, 2, n) for n in range(1, 9)]
    inp = SolverInput(2027, 2, [PersonInput(1, Role.A)], days, {})
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    assert objectives.ordered_terms(model, x, inp)[0][0] == "ordinary_rest_spacing"
