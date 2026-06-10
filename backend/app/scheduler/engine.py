"""CP-SAT scheduling engine (spec §5).

``SchedulerEngine.solve`` builds the model (decision variables → hard
constraints §5.3 → soft objectives §5.4), runs OR-Tools with a time limit, and
returns a ``SolverOutput``. On infeasibility it reports back so the admin can
adjust / edit manually (§5.6).

Scope note: the engine auto-assigns only the core codes in
``ASSIGNABLE_CODES``. Other codes (B, T, O/D, AD, AL, CD, S) are admin-entered
or pre-pinned via ``SolverInput.approved_off``.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import constraints, objectives
from app.scheduler.domain import AssignmentResult, SolverInput, SolverOutput, Violation

ASSIGNABLE_CODES: tuple[AttendanceCode, ...] = (
    AttendanceCode.A,
    AttendanceCode.D,
    AttendanceCode.A_D,
    AttendanceCode.X,
)


class SchedulerEngine:
    def __init__(self, assignable_codes: tuple[AttendanceCode, ...] = ASSIGNABLE_CODES):
        self.assignable_codes = tuple(assignable_codes)

    def solve(self, inp: SolverInput) -> SolverOutput:
        model = cp_model.CpModel()
        x = self._build_vars(model, inp)

        constraints.add_all(model, x, inp, self.assignable_codes)
        objectives.add_all(model, x, inp, self.assignable_codes)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = inp.max_solve_seconds
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return SolverOutput(feasible=True, assignments=self._extract(solver, x))

        # §5.6 — report infeasibility; the service can suggest A/D fallback and
        # the admin can finish the schedule manually (F-09).
        return SolverOutput(
            feasible=False,
            violations=[
                Violation(
                    rule="infeasible",
                    message="No valid schedule found for the given constraints (§5.6).",
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
