"""§5.4 #7 — balance A and D shift counts across the fixed group (soft).

Highest-priority objective (spec note): within the month, minimize the spread
between the person with the most and the fewest A shifts — and likewise for D
— across the FIXED group (A1–A4), the roles that actually take flight duty.

An ``A/D`` double shift covers one arrival and one departure, so it counts
toward BOTH totals. Flexible roles (M/T) default to O/D and are excluded —
including them would just measure who isn't on flight duty.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    fixed = [p for p in inp.people if p.role.is_fixed]
    if len(fixed) < 2:
        return []  # spread needs at least two people

    n_days = len(inp.days)
    penalties: list[cp_model.LinearExpr] = []

    for shift in (AttendanceCode.A, AttendanceCode.D):
        totals: list[cp_model.IntVar] = []
        for p in fixed:
            total = model.NewIntVar(0, n_days, f"total_{shift.name}_{p.user_id}")
            # A/D counts toward both A and D totals (§5.3 #6 / §7).
            model.Add(
                total
                == sum(x[(p.user_id, d, shift)] for d in inp.days)
                + sum(x[(p.user_id, d, AttendanceCode.A_D)] for d in inp.days)
            )
            totals.append(total)

        hi = model.NewIntVar(0, n_days, f"max_{shift.name}")
        lo = model.NewIntVar(0, n_days, f"min_{shift.name}")
        model.AddMaxEquality(hi, totals)
        model.AddMinEquality(lo, totals)
        penalties.append(weight * (hi - lo))

    return penalties
