"""Premium-off fairness across months (locked decision #6, extends §5.4 #8).

An OFF (X) day landing on a Saturday, Sunday or public holiday is a "premium
off" — holidays are normal working days (decision #5), so being off on one is
a perk, exactly like a weekend. Whoever received more premium offs in past
months yields priority: each person's month total is offset by their
``carry_premium_off`` and the spread (max − min) across ALL people is
minimized. F-14 (phase 07) persists the updated carry after month close.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput

SATURDAY, SUNDAY = 5, 6  # date.weekday()


def premium_days(inp: SolverInput) -> list[date]:
    """Sat/Sun/holiday days of the month (holiday = premium marker only)."""
    return [
        d
        for d in sorted(inp.days)
        if d.weekday() in (SATURDAY, SUNDAY) or d in inp.holidays
    ]


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    if len(inp.people) < 2:
        return []

    prem = premium_days(inp)
    if not prem:
        return []

    max_carry = max(p.carry_premium_off for p in inp.people)
    bound = len(prem) + max_carry

    totals: list[cp_model.IntVar] = []
    for p in inp.people:
        total = model.NewIntVar(0, bound, f"premium_{p.user_id}")
        # History (carry) + this month's premium X days.
        model.Add(
            total
            == p.carry_premium_off
            + sum(x[(p.user_id, d, AttendanceCode.X)] for d in prem)
        )
        totals.append(total)

    hi = model.NewIntVar(0, bound, "premium_max")
    lo = model.NewIntVar(0, bound, "premium_min")
    model.AddMaxEquality(hi, totals)
    model.AddMinEquality(lo, totals)
    return [weight * (hi - lo)]
