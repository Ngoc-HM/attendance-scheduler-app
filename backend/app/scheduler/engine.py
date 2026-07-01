"""CP-SAT scheduling engine (spec §5) — rule-based, NO ML/AI (§9.6).

``SchedulerEngine.solve`` builds the model (decision variables → hard
constraints §5.3 → soft objectives §5.4 → slack penalties), runs OR-Tools
with a time limit and returns a ``SolverOutput``.

Always-feasible architecture (locked decision #2): staffing and off-day rules
carry penalized slack, so a solution is returned even when rules cannot all
hold — each broken rule comes back as a ``Violation`` (§5.6 #12–14) for the
admin to resolve (A/D fallback suggestion, manual edit F-09).

Role-aware model (owner decision 2026-06-26):
    Role.A (fixed group): {A, D, A/D, X, CD} — full flight rules + comp days.
    Role.T (flexible):    {AD, X}            — full-day duty, no shift split.
    Role.M (admin):       {O/D, X}           — office duty.

Variable domains are built PER PERSON from ``role_codes.codes_for(role)``.
The legacy ``ASSIGNABLE_CODES`` constant is kept for backward-compat import;
it is no longer used as the per-person var domain inside the engine.

Flight-staffing demand, balance, A/D usage, and comp-day constraints are
scoped to role-A people only (they are the only ones with A/D/A_D vars).
Off-day (2 X/block), consecutive-working, and off-chain rules apply to ALL
roles, each using their own working-code set for "working" detection.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

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
    AttendanceCode.A_D,
    AttendanceCode.X,
    AttendanceCode.CD,
)


class SchedulerEngine:
    def __init__(self, assignable_codes: tuple[AttendanceCode, ...] = ASSIGNABLE_CODES):
        # assignable_codes kept as parameter for API compat; ignored internally.
        self.assignable_codes = tuple(assignable_codes)

    def solve(self, inp: SolverInput) -> SolverOutput:
        model = cp_model.CpModel()
        x = self._build_vars(model, inp)
        registry = SlackRegistry()

        constraints.add_all(model, x, inp, registry)
        soft_terms = objectives.add_all(model, x, inp)
        model.Minimize(sum(registry.penalty_terms()) + sum(soft_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = inp.max_solve_seconds
        # Determinism for tests/reproducibility (§5.6 — same input, same plan).
        solver.parameters.random_seed = 42
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return SolverOutput(
                feasible=True,
                assignments=self._extract(solver, x),
                # Slack > 0 → rule could not hold; admin resolves (§5.6).
                violations=registry.violations(solver),
            )

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
                    x[(p.user_id, d, c)] = model.NewBoolVar(
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
            if solver.Value(var) == 1:
                results.append(AssignmentResult(user_id=uid, day=d, code=code))
        return results
