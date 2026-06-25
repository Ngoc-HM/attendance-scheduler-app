"""§5.4 #7 — balance A and D shift counts across ALL people (soft).

Highest-priority objective (spec note): within the month, minimize the spread
between the person with the most and the fewest A shifts — and likewise for D.
Every role now takes flight duty (O/D is no longer auto-assigned; manual roster
WR JUN26 shows M/T on A/D too), so the balance spans the whole team, not just
the fixed A group.

An ``A/D`` double shift covers one arrival and one departure, so it counts
toward BOTH totals.
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
    people = inp.people
    if len(people) < 2:
        return []  # spread needs at least two people

    n_days = len(inp.days)
    penalties: list[cp_model.LinearExpr] = []

    for shift in (AttendanceCode.A, AttendanceCode.D):
        totals: list[cp_model.IntVar] = []
        for p in people:
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
