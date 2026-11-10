"""Someone of each role group is at work every day (owner 2026-11-10).

Role groups are people with the same role (``role_codes.role_groups``, 2+
members). Per group and per day, a penalty when EVERY member is off — X or
CD, chosen or pinned leave — so the good day-off pairs are taken in turns
rather than by the whole group at once. Group A is mostly covered by flight
staffing already; this matters for F, M and T, which have no staffing floor.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import OFF_CODES, codes_for, role_groups


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    penalties: list[cp_model.LinearExpr] = []
    for group in role_groups(inp.people):
        off_codes = [c for c in codes_for(group[0].role) if c in OFF_CODES]
        role = group[0].role.value
        for d in inp.days:
            off = [x[(p.user_id, d, c)] for p in group for c in off_codes]
            all_off = model.new_bool_var(f"all_off_{role}_{d.isoformat()}")
            # all_off >= 1 when every member is off (each member has exactly
            # one code, so sum(off) == len(group) means all of them).
            model.add(sum(off) - (len(group) - 1) <= all_off)
            penalties.append(weight * all_off)
    return penalties
