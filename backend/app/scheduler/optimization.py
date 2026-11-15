"""Ordered CP-SAT objectives with a single deadline and retained incumbents."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from ortools.sat.python import cp_model


@dataclass
class OptimizationResult:
    solver: cp_model.CpSolver | None
    status: str
    diagnostics: list[dict[str, object]]
    first_stage_proven: bool = False


def solve_ordered(
    model: cp_model.CpModel,
    stages: list[tuple[str, cp_model.LinearExprT]],
    *,
    deadline: float,
    solver_factory: Callable[[float], cp_model.CpSolver],
    first_time_share: float = 0.4,
    remaining_stages_builder: Callable[[], list[tuple[str, cp_model.LinearExprT]]] | None = None,
) -> OptimizationResult:
    """Freeze each achieved objective before searching a lower priority.

    A timed-out stage may leave an unproven incumbent; its achieved value is
    preserved, with truthful proof flags. A later UNKNOWN never replaces an
    earlier plan. If the first search finds nothing, retry its SAME objective
    with the remaining budget; never mix rules and preferences in a fallback.
    Optional later-stage helpers are built after the rule incumbent is found,
    so their presolve complexity cannot obstruct finding a valid roster.
    """
    incumbent = None
    diagnostics: list[dict[str, object]] = []
    all_proven = True
    first_proven = False
    completed = 0
    for index, (name, expression) in enumerate(stages):
        remaining = max(0.0, deadline - time.monotonic())
        if remaining <= 0:
            break
        model.minimize(expression)
        stages_left = len(stages) - index
        budget = remaining * first_time_share if index == 0 else remaining / stages_left
        solver = None
        status = cp_model.UNKNOWN
        for attempt in range(2 if incumbent is None else 1):
            if attempt:
                budget = max(0.0, deadline - time.monotonic())
                if budget <= 0:
                    break
            candidate = solver_factory(budget)
            started = time.monotonic()
            status = candidate.solve(model)
            found = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
            diagnostics.append(
                {
                    "name": name,
                    "status": candidate.status_name(status).lower(),
                    "value": int(candidate.value(expression)) if found else None,
                    "best_bound": float(candidate.best_objective_bound) if found else None,
                    "proven_optimal": status == cp_model.OPTIMAL,
                    "seconds": max(0.0, time.monotonic() - started),
                }
            )
            if found:
                solver = candidate
                break
            if status != cp_model.UNKNOWN:
                break
        if solver is None:
            if incumbent is None:
                state = (
                    "infeasible"
                    if status in (cp_model.INFEASIBLE, cp_model.MODEL_INVALID)
                    else "unknown"
                )
                return OptimizationResult(None, state, diagnostics)
            break

        incumbent = solver
        proven = status == cp_model.OPTIMAL
        all_proven = all_proven and proven
        if index == 0:
            first_proven = proven
        completed += 1
        # Equality avoids any later stage silently trading one higher-priority
        # achieved value for another; every frozen expression is exact integer.
        model.add(expression == solver.value(expression))
        model.clear_hints()
        for var_index in range(len(model.proto.variables)):
            var = model.get_int_var_from_proto_index(var_index)
            model.add_hint(var, solver.value(var))
        if index == 0 and remaining_stages_builder is not None:
            # Build AFTER recording hints: the incumbent response has no
            # values for these new helpers. Partial hints remain valid.
            stages.extend(remaining_stages_builder())

    complete = completed == len(stages)
    state = "optimal" if complete and all_proven else "feasible" if incumbent else "unknown"
    return OptimizationResult(incumbent, state, diagnostics, first_proven)
