"""§5.4 #7 — balance A and D shift counts ACROSS role-A people (soft).

Scoped to ROLE-A people only (owner decision 2026-06-26 — only the fixed group
A takes A or D flight duties; M→O/D, T/F→AD are not flight-scheduled).

Per spec §5.4: minimise the spread (max − min) of monthly A totals across
role-A people, and likewise for D totals. A separate objective minimizes each
person's own A-versus-D gap as far as flight demand allows. Emergency A/D is
not part of an automatic solver run.
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
    """Cross-people A-versus-D spread penalties for role-A people."""
    role_a = [p for p in inp.people if p.role is Role.A]
    if len(role_a) < 2:
        return []  # a spread needs at least two people

    n_days = len(inp.days)
    penalties: list[cp_model.LinearExpr] = []

    for shift in (AttendanceCode.A, AttendanceCode.D):
        totals: list[cp_model.IntVar] = []
        for p in role_a:
            total = model.NewIntVar(0, n_days, f"total_{shift.name}_{p.user_id}")
            model.Add(
                total
                == sum(x[(p.user_id, d, shift)] for d in inp.days)
            )
            totals.append(total)

        hi = model.NewIntVar(0, n_days, f"max_{shift.name}")
        lo = model.NewIntVar(0, n_days, f"min_{shift.name}")
        model.AddMaxEquality(hi, totals)
        model.AddMinEquality(lo, totals)
        penalties.append(weight * (hi - lo))

    return penalties


def individual_terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    """Minimize |A-total - D-total| separately for every role-A person.

    Emergency A/D is intentionally outside the automatic solver domain.
    """
    n_days = len(inp.days)
    penalties: list[cp_model.LinearExpr] = []
    for person in inp.people:
        if person.role is not Role.A:
            continue
        total_a = sum(
            x[(person.user_id, day, AttendanceCode.A)]
            for day in inp.days
        )
        total_d = sum(
            x[(person.user_id, day, AttendanceCode.D)]
            for day in inp.days
        )
        gap = model.NewIntVar(0, n_days, f"individual_ad_gap_{person.user_id}")
        model.AddAbsEquality(gap, total_a - total_d)
        penalties.append(weight * gap)
    return penalties
