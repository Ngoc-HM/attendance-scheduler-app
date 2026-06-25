"""CP-SAT scheduling engine (spec §5) — rule-based, NO ML/AI (§9.6).

``SchedulerEngine.solve`` builds the model (decision variables → hard
constraints §5.3 → soft objectives §5.4 → slack penalties), runs OR-Tools
with a time limit and returns a ``SolverOutput``.

Always-feasible architecture (locked decision #2): staffing and off-day rules
carry penalized slack, so a solution is returned even when rules cannot all
hold — each broken rule comes back as a ``Violation`` (§5.6 #12–14) for the
admin to resolve (A/D fallback suggestion, manual edit F-09).

Scope note: the engine auto-assigns only ``ASSIGNABLE_CODES`` — flight duties
(A / D / A/D) plus the two rest codes (X weekly off, CD comp-day). Every working
day for every role is a real flight shift, matching the manual roster (WR JUN26):
the per-day flightPairs staffing is a *minimum* floor and everyone on duty gets
A or D, balanced. O/D (office duty) is NO LONGER auto-generated — it stays in
the code set only for admin manual entry / attendance (e.g. a cancelled flight,
"VN31/30 NO-OP"). Other codes (B, T, AD, AL, S) are admin-entered or pre-pinned
via ``SolverInput.approved_off``.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import constraints, objectives
from app.scheduler.domain import AssignmentResult, SolverInput, SolverOutput, Violation
from app.scheduler.slack_registry import SlackRegistry

ASSIGNABLE_CODES: tuple[AttendanceCode, ...] = (
    AttendanceCode.A,
    AttendanceCode.D,
    AttendanceCode.A_D,
    AttendanceCode.X,
    AttendanceCode.CD,   # auto comp-day off — forced from carry_comp (§5.3 #6)
)


class SchedulerEngine:
    def __init__(self, assignable_codes: tuple[AttendanceCode, ...] = ASSIGNABLE_CODES):
        self.assignable_codes = tuple(assignable_codes)

    def solve(self, inp: SolverInput) -> SolverOutput:
        model = cp_model.CpModel()
        x = self._build_vars(model, inp)
        registry = SlackRegistry()

        constraints.add_all(model, x, inp, self.assignable_codes, registry)
        soft_terms = objectives.add_all(model, x, inp, self.assignable_codes)
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
        x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar] = {}
        for p in inp.people:
            for d in inp.days:
                for c in self.assignable_codes:
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
