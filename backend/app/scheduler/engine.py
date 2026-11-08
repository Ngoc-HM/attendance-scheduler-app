"""CP-SAT scheduling engine (spec §5) — rule-based, NO ML/AI (§9.6).

``SchedulerEngine.solve`` builds the model (decision variables → hard
constraints §5.3 → soft objectives §5.4 → slack penalties), runs OR-Tools in
two phases (slack only, then the soft objectives at that slack) within the
time limit and returns a ``SolverOutput`` with the solver status.

Always-feasible architecture (locked decision #2): staffing and off-day rules
carry penalized slack, so a solution is returned even when rules cannot all
hold — each broken rule comes back as a ``Violation`` (§5.6 #12–14) for the
admin to resolve without automatically forcing a double shift.

Role-aware model (owner decision 2026-06-26):
    Role.A (fixed group): {A, D, X, CD}  — full flight rules + comp days.
    Role.T (flexible):    {AD, X, CD}     — full-day duty, no shift split.
    Role.M (admin):       {O/D, X, CD}    — office duty.
    Role.F (split of T):  {AD, X, CD}     — T-like: weekly-2-off AND the
                                            max-5-consecutive-working rule
                                            apply (owner 2026-07-22).

Variable domains are built PER PERSON from ``role_codes.codes_for(role)``.
The legacy ``ASSIGNABLE_CODES`` constant is kept for backward-compat import;
it is no longer used as the per-person var domain inside the engine.

Flight-staffing demand and A-versus-D balance are scoped to role-A people
only. Emergency A/D is outside the automatic solver domain. Comp days (CD
granted against carried debt — holiday work earns it for every role, owner D1
2026-11-06), off-day (2 X/block), rolling-seven-day rest, consecutive-working,
and off-chain rules apply to ALL roles, using each role's own working-code set.
"""

from __future__ import annotations

import math
import time
from datetime import date

from ortools.sat.python import cp_model

from app.core.config import settings
from app.models.enums import AttendanceCode
from app.scheduler import constraints, objectives
from app.scheduler.domain import AssignmentResult, SolverInput, SolverOutput, Violation
from app.scheduler.role_codes import codes_for
from app.scheduler.slack_registry import SlackRegistry

# Kept for backward-compat: external code that imports ASSIGNABLE_CODES still
# works.  Inside the engine, per-person domains come from codes_for(p.role).
ASSIGNABLE_CODES: tuple[AttendanceCode, ...] = (
    AttendanceCode.A,
    AttendanceCode.D,
    AttendanceCode.X,
    AttendanceCode.CD,
)

# Share of ``max_solve_seconds`` for phase 1 (slack only); phase 2 gets the
# rest, including whatever phase 1 did not use.
PHASE1_TIME_SHARE = 0.4


class SchedulerEngine:
    def __init__(
        self,
        assignable_codes: tuple[AttendanceCode, ...] = ASSIGNABLE_CODES,
        *,
        num_workers: int | None = None,
    ):
        # assignable_codes kept as parameter for API compat; ignored internally.
        self.assignable_codes = tuple(assignable_codes)
        # None → settings.SOLVER_NUM_WORKERS, read at solve time.
        self.num_workers = num_workers

    def solve(self, inp: SolverInput) -> SolverOutput:
        """Solve in two phases (lexicographic: slack first, then soft terms).

        Phase 1 minimises the weighted slack alone — the cheap question "which
        rules must break?" — with ``PHASE1_TIME_SHARE`` of the time limit.
        Phase 2 keeps the slack total within phase 1's result (and at or above
        its proven bound), starts from phase 1's plan as a hint and minimises
        the soft objectives with the remaining time. One combined objective
        used to stop at the time limit on a 1-CPU machine with invented slack
        although a clean plan existed (review C1).
        """
        model = cp_model.CpModel()
        x = self._build_vars(model, inp)
        registry = SlackRegistry()

        constraints.add_all(model, x, inp, registry)
        soft_terms = objectives.add_all(model, x, inp)
        slack = sum(registry.penalty_terms())

        started = time.monotonic()
        model.minimize(slack)
        phase1 = self._solver(inp.max_solve_seconds * PHASE1_TIME_SHARE)
        status1 = phase1.solve(model)
        if status1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self._no_schedule(status1)

        slack_found = round(phase1.objective_value)
        # Proven lower bound on the slack (equals slack_found when OPTIMAL).
        slack_floor = math.ceil(phase1.best_objective_bound - 1e-6)
        fallback = SolverOutput(
            feasible=True,
            assignments=self._extract(phase1, x),
            # Slack > 0 → rule could not hold; admin resolves (§5.6).
            violations=registry.violations(phase1),
            status="feasible",
            slack_proven_minimal=slack_found <= slack_floor,
        )

        model.add(slack <= slack_found)
        if slack_floor > 0:
            model.add(slack >= slack_floor)
        for var in x.values():
            model.add_hint(var, phase1.value(var))
        # The slack stays in the objective: when phase 1 was not proven
        # optimal, phase 2 may still lower it (weights keep it lexicographic).
        model.minimize(slack + sum(soft_terms))
        remaining = max(inp.max_solve_seconds - (time.monotonic() - started), 0.0)
        phase2 = self._solver(remaining)
        status2 = phase2.solve(model)
        if status2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            # Out of time before improving on the hint: keep phase 1's plan.
            return fallback

        both_optimal = status1 == cp_model.OPTIMAL and status2 == cp_model.OPTIMAL
        return SolverOutput(
            feasible=True,
            assignments=self._extract(phase2, x),
            violations=registry.violations(phase2),
            status="optimal" if both_optimal else "feasible",
            slack_proven_minimal=phase2.value(slack) <= slack_floor,
        )

    def _solver(self, max_seconds: float) -> cp_model.CpSolver:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_seconds
        # A fixed worker count and seed (§5.6 — same input, same plan). With
        # one worker a run that finishes inside the time limit is
        # reproducible; one stopped by the limit depends on machine speed.
        workers = self.num_workers
        if workers is None:
            workers = settings.SOLVER_NUM_WORKERS
        solver.parameters.num_workers = workers
        solver.parameters.random_seed = 42
        return solver

    @staticmethod
    def _no_schedule(status: cp_model.CpSolverStatus) -> SolverOutput:
        # With the slack architecture this only happens on contradictory
        # PINS (e.g. approved-off cell that another hard rule forbids) or a
        # too-small time limit (§5.6 #12).
        return SolverOutput(
            feasible=False,
            violations=[
                Violation(
                    rule="infeasible",
                    message=(
                        "No schedule found: contradictory pinned inputs or "
                        "solver time limit reached (§5.6)."
                    ),
                )
            ],
            status=(
                "infeasible"
                if status in (cp_model.INFEASIBLE, cp_model.MODEL_INVALID)
                else "unknown"
            ),
        )

    def _build_vars(
        self, model: cp_model.CpModel, inp: SolverInput
    ) -> dict[tuple[int, date, AttendanceCode], cp_model.IntVar]:
        """Build one BoolVar per (person, day, code) for the person's role domain."""
        x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar] = {}
        for p in inp.people:
            person_codes = codes_for(p.role)
            for d in inp.days:
                for c in person_codes:
                    x[(p.user_id, d, c)] = model.new_bool_var(
                        f"x_{p.user_id}_{d.isoformat()}_{c.name}"
                    )
        return x

    @staticmethod
    def _extract(
        solver: cp_model.CpSolver,
        x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    ) -> list[AssignmentResult]:
        results: list[AssignmentResult] = []
        for (uid, d, code), var in x.items():
            if solver.value(var) == 1:
                results.append(AssignmentResult(user_id=uid, day=d, code=code))
        return results
