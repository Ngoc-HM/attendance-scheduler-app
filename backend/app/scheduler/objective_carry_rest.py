"""Group A rests on the carry days as much as the flights allow.

The carry days (the next month's days a roster runs into, owner 2026-11-18)
have no X minimum, only a cap. Left alone, the solver may keep more group-A
people on duty there than the flights need. Group A's month is tight — with
the usual flights its spare days equal exactly the month's ordinary X — so
every needless duty on the carry days is an X the next month can no longer
give (found 2026-11-20: January came out short after December's carry days).

Per group-A person and per carry-day block: the gap between the block's cap
(its Saturdays and Sundays, ``constraints_monthly_quota``) and the X taken.
Minimised right after the rules, so staffing and the rest rules still win.
Groups without flight duty are left out: their month always has room.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.calendar_utils import month_groups
from app.scheduler.carried import ahead_days
from app.scheduler.domain import SolverInput
from app.scheduler.objective_monthly_off_target import entitlement


def terms(
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExprT]:
    gaps: list[cp_model.LinearExprT] = []
    for days in month_groups(ahead_days(inp)):
        for person in inp.people:
            if person.role is not Role.A:
                continue
            uid = person.user_id
            pinned = inp.approved_off.get(uid, {})
            cap = entitlement(days, pinned)
            gaps.append(
                cap - sum(x[(uid, d, AttendanceCode.X)] for d in days if d not in pinned)
            )
    return gaps
