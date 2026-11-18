"""Exact monthly ordinary-X entitlement, with explicit diagnostic slack.

Approved leave is represented by X in the decision layer but is not ordinary
rest. CD is additional to ordinary X. The shared target preserves the existing
weekend-leave adjustment, so approved leave never creates make-up duties.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput
from app.scheduler.objective_monthly_off_target import target
from app.scheduler.slack_registry import SlackRegistry


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    for person in inp.people:
        if person.role is Role.F:
            continue  # group F rests by the week (``role_f``), not by the month
        uid = person.user_id
        pinned = inp.approved_off.get(uid, {})
        chosen = sum(x[(uid, d, AttendanceCode.X)] for d in inp.days if d not in pinned)
        entitlement = target(inp, uid)
        under = model.new_int_var(0, len(inp.days), f"monthly_off_under_{uid}")
        over = model.new_int_var(0, len(inp.days), f"monthly_off_over_{uid}")
        model.add(chosen + under - over == entitlement)
        for slack, direction in ((under, "shortfall"), (over, "excess")):
            registry.register(
                slack,
                rule=f"monthly_off_{direction}",
                user_id=uid,
                message=f"User {uid}: monthly ordinary X {direction} (target {entitlement})",
                params={"target": entitlement},
            )
