"""Priority and timeout contracts exercised with real CP-SAT searches."""

import time

from ortools.sat.python import cp_model

from app.scheduler import optimization


def _factory(seconds):
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = seconds
    return solver


def test_lower_preference_cannot_buy_a_higher_priority_loss():
    model = cp_model.CpModel()
    breach = model.new_bool_var("breach")
    result = optimization.solve_ordered(
        model,
        [("rules", breach), ("preference", -1000000 * breach)],
        deadline=time.monotonic() + 2,
        solver_factory=_factory,
    )
    assert result.solver.value(breach) == 0
    assert result.status == "optimal"
    assert result.diagnostics[0]["proven_optimal"] is True


def test_later_timeout_retains_incumbent_and_does_not_claim_optimal():
    model = cp_model.CpModel()
    chosen = model.new_int_var(0, 5, "chosen")
    calls = 0

    def later_timeout(seconds):
        nonlocal calls
        calls += 1
        return _factory(seconds if calls == 1 else 0)

    result = optimization.solve_ordered(
        model,
        [("rules", chosen), ("preference", -chosen)],
        deadline=time.monotonic() + 2,
        solver_factory=later_timeout,
    )
    assert result.solver.value(chosen) == 0
    assert result.status == "feasible"
    assert result.diagnostics[-1]["status"] == "unknown"


def test_initial_unknown_retries_same_priority_without_weighted_fallback():
    model = cp_model.CpModel()
    breach = model.new_bool_var("breach")
    calls = 0

    def first_timeout(seconds):
        nonlocal calls
        calls += 1
        return _factory(0 if calls == 1 else seconds)

    result = optimization.solve_ordered(
        model,
        [("rules", breach), ("preference", -1000000 * breach)],
        deadline=time.monotonic() + 2,
        solver_factory=first_timeout,
    )
    assert result.solver.value(breach) == 0
    assert result.diagnostics[0]["status"] == "unknown"
    assert result.diagnostics[1]["name"] == "rules"
    assert result.status == "optimal"


def test_all_solver_calls_share_one_deadline(monkeypatch):
    model = cp_model.CpModel()
    chosen = model.new_bool_var("chosen")
    clock = [100.0]
    monkeypatch.setattr(optimization.time, "monotonic", lambda: clock[0])
    budgets = []

    class TimedSolver:
        def __init__(self, seconds):
            budgets.append(seconds)
            self.wrapped = _factory(seconds)

        def solve(self, model):
            status = self.wrapped.solve(model)
            clock[0] += 0.15
            return status

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

    result = optimization.solve_ordered(
        model,
        [("first", chosen), ("second", -chosen), ("third", chosen)],
        deadline=100.25,
        solver_factory=TimedSolver,
    )
    assert len(budgets) == 2
    assert budgets[0] <= 0.25
    assert budgets[1] <= 0.100001
    assert result.solver.value(chosen) == 0
    assert result.status == "feasible"


def test_later_objective_helpers_are_built_after_rule_search():
    model = cp_model.CpModel()
    breach = model.new_bool_var("breach")
    model_sizes = []

    def factory(seconds):
        model_sizes.append(len(model.proto.variables))
        return _factory(seconds)

    def later_stages():
        helper = model.new_int_var(0, 100, "later_helper")
        model.add(helper == 100 * breach)
        return [("later", -helper)]

    result = optimization.solve_ordered(
        model,
        [("rules", breach)],
        deadline=time.monotonic() + 2,
        solver_factory=factory,
        remaining_stages_builder=later_stages,
    )
    assert model_sizes == [1, 2]
    assert result.solver.value(breach) == 0
    assert result.status == "optimal"
