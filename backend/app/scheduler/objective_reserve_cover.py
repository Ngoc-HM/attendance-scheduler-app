"""Reserve cover: three group-A people at work on every flight day (owner 2026-11-12).

Owner: "Vẫn phải đảm bảo 2 chuyến bay thì 1A 2D, 1 chuyến bay 1A 1D, nhưng
dự phòng có người nghỉ thì vẫn phải để cho có 3 người trực ngày hôm đó (quy
tắc mềm, không bắt buộc)."

The staffing floor (``constraints_staffing``) is unchanged and stays a
reported rule. On top of it, on every day with flights, ``min(3, number of
role-A people)`` of them should be at work, so one is in reserve when
somebody drops out. Each person missing below that costs ``weight``. It only
bites on one-pair days (floor: 2 people); a two-pair day already needs 3.

An objective term, never a slack: nothing is reported when only 2 work on a
one-pair day, and the month's X target (``monthly_off_target``) outranks it.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import OFF_CODES, codes_for

RESERVE = 3


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    group_a = [p for p in inp.people if p.role is Role.A]
    want = min(RESERVE, len(group_a))
    if not want:
        return []
    working = [c for c in codes_for(Role.A) if c not in OFF_CODES]
    penalties: list[cp_model.LinearExpr] = []
    for d in sorted(inp.days):
        if inp.flight_pairs.get(d, 0) <= 0:
            continue
        at_work = sum(x[(p.user_id, d, c)] for p in group_a for c in working)
        short = model.new_int_var(0, want, f"reserve_short_{d.isoformat()}")
        model.add(short >= want - at_work)  # minimised, so = max(0, want − at work)
        penalties.append(weight * short)
    return penalties
