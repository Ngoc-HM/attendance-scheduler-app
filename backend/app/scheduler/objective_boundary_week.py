"""Consecutive-work look-ahead using only known next-month flight demand.

There is no weekly rest debt. Project role-A work/rest choices over the first
five next-month days and require every crossing six-day window to contain
rest. Penalize projected staffing shortfall only where flight data exists;
unknown days create no demand. The next generation still checks actual carry.
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import OFF_CODES, codes_for

NEED = {0: 0, 1: 2, 2: 3}


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    days = sorted(inp.days)
    people = [p for p in inp.people if p.role is Role.A]
    if not days or not people:
        return []
    ahead = [days[-1] + timedelta(days=n) for n in range(1, 6)]
    known = [d for d in ahead if d in inp.next_flight_pairs]
    if not known:
        return []
    tail = days[-5:]
    working = [c for c in codes_for(Role.A) if c not in OFF_CODES]
    projected = {
        (p.user_id, d): model.new_bool_var(f"next_work_{p.user_id}_{d}")
        for p in people
        for d in ahead
    }
    for p in people:
        timeline = [sum(x[(p.user_id, d, c)] for c in working) for d in tail]
        timeline += [projected[(p.user_id, d)] for d in ahead]
        for start in range(len(timeline) - 5):
            model.add(sum(timeline[start : start + 6]) <= 5)
    penalties = []
    for d in known:
        need = NEED[inp.next_flight_pairs[d]]
        if need == 0:
            continue
        shortage = model.new_int_var(0, need, f"next_staffing_short_{d}")
        model.add(sum(projected[(p.user_id, d)] for p in people) + shortage >= need)
        penalties.append(weight * shortage)
    return penalties
