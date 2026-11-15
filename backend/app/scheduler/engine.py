"""CP-SAT scheduling engine (spec §5) — rule-based, NO ML/AI (§9.6).

``SchedulerEngine.solve`` builds the model (decision variables → hard
constraints §5.3 → soft objectives §5.4 → slack penalties), runs OR-Tools in
ordered stages (rules, individual A/D fairness, rest turns, preferences)
within one time limit and returns a ``SolverOutput`` with the solver status.

Always-feasible architecture (locked decision #2): staffing and rest rules
carry penalized slack, so a solution is returned even when rules cannot all
hold — each broken rule comes back as a ``Violation`` (§5.6 #12–14) for the
admin to resolve without automatically forcing a double shift.

Role-aware model (owner decision 2026-06-26):
    Role.A (fixed group): {A, D, X, CD}  — full flight rules + comp days.
    Role.T (flexible):    {AD, X, CD}     — full-day duty, no shift split.
    Role.M (admin):       {O/D, X, CD}    — office duty.
    Role.F (split of T):  {AD, X, CD}     — T-like: monthly rest and
                                            max-5-consecutive-working rules
                                            apply (owner 2026-07-22).

Variable domains are built PER PERSON from ``role_codes.codes_for(role)``.
The legacy ``ASSIGNABLE_CODES`` constant is kept for backward-compat import;
it is no longer used as the per-person var domain inside the engine.

Flight-staffing demand and A-versus-D balance are scoped to role-A people
only. Emergency A/D is outside the automatic solver domain. Comp days (CD
granted against carried debt — holiday work earns it for every role, owner D1
2026-11-06), monthly rest entitlement, consecutive-working
and off-chain rules apply to ALL roles, using each role's own working-code set.
"""

from __future__ import annotations

import time
from datetime import date

from ortools.sat.python import cp_model

from app.core.config import settings
from app.models.enums import AttendanceCode
from app.scheduler import constraints, objectives
from app.scheduler.domain import AssignmentResult, SolverInput, SolverOutput, Violation
from app.scheduler.optimization import solve_ordered
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

# Initial share of the remaining deadline for rule slack; later stages
# divide the remainder and preserve every achieved higher-stage value.
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
        """Optimize named priorities under one wall-clock deadline.

        Model construction uses the same budget. Achieved higher objectives
        are frozen before lower preferences, and a later timeout returns the
        most recent incumbent with its original rule violations.
        """
        deadline = time.monotonic() + max(0.0, inp.max_solve_seconds)
        model = cp_model.CpModel()
        x = self._build_vars(model, inp)
        registry = SlackRegistry()
        constraints.add_all(model, x, inp, registry)
        stages: list[tuple[str, cp_model.LinearExprT]] = [
            ("rules", sum(registry.penalty_terms()))
        ]
        result = solve_ordered(
            model,
            stages,
            deadline=deadline,
            solver_factory=self._solver,
            first_time_share=PHASE1_TIME_SHARE,
            remaining_stages_builder=lambda: objectives.ordered_terms(model, x, inp),
        )
        if result.solver is None:
            out = self._no_schedule(
                cp_model.INFEASIBLE if result.status == "infeasible" else cp_model.UNKNOWN
            )
            out.phase_diagnostics = result.diagnostics
            return out
        return SolverOutput(
            feasible=True,
            assignments=self._extract(result.solver, x),
            violations=registry.violations(result.solver),
            status=result.status,
            slack_proven_minimal=result.first_stage_proven,
            phase_diagnostics=result.diagnostics,
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
