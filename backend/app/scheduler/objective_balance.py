"""§5.4 #7 — balance A and D shift counts ACROSS role-A people (soft).

Scoped to ROLE-A people only (owner decision 2026-06-26 — only the fixed group
A takes A/D flight duties; M→O/D, T→AD are not flight-scheduled).

Per spec §5.4: minimise the spread (max − min) of monthly A totals across
role-A people, and likewise for D totals. An ``A/D`` double-shift covers one
arrival and one departure, so it counts toward BOTH totals.

NOTE (owner 2026-06-26): balance here is CROSS-PEOPLE — every role-A person
gets a fair, equal share of the A and the D shifts — NOT per-person A≈D. The
HARD staffing rule (§5.3 #4: a 2-pair day needs 1 person on A and 2 on D)
structurally requires more D than A on busy days, so making each individual's
A-count equal their D-count is mathematically impossible and is intentionally
not attempted.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    """Cross-people A/D spread penalties for role-A people."""
    role_a = [p for p in inp.people if p.role is Role.A]
    if len(role_a) < 2:
        return []  # a spread needs at least two people

    n_days = len(inp.days)
    penalties: list[cp_model.LinearExpr] = []

    for shift in (AttendanceCode.A, AttendanceCode.D):
        totals: list[cp_model.IntVar] = []
        for p in role_a:
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
