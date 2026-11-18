"""Exact monthly ordinary-X entitlement, with explicit diagnostic slack.

Approved leave is represented by X in the decision layer but is not ordinary
rest. CD is additional to ordinary X. The shared target preserves the existing
weekend-leave adjustment, so approved leave never creates make-up duties.

The target counts over the window's OWN month, its carried cells included
as facts. The carry days of the next month (owner 2026-11-18) have no X
minimum and at most as many X as they hold Saturdays and Sundays (same
leave adjustment): that month's own exact count, with these days as facts,
makes up the rest over its remaining days.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.calendar_utils import month_groups
from app.scheduler.carried import ahead_days, own_days
from app.scheduler.domain import SolverInput
from app.scheduler.objective_monthly_off_target import entitlement, target
from app.scheduler.slack_registry import SlackRegistry

# Message variant of ``monthly_off_excess`` for the carry days.
CARRY_KEY = "monthly_off_excess_carry"


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    ahead = month_groups(ahead_days(inp))
    for person in inp.people:
        if person.role is Role.F:
            continue  # group F rests by the week (``role_f``), not by the month
        uid = person.user_id
        pinned = inp.approved_off.get(uid, {})
        own = own_days(inp)
        chosen = sum(x[(uid, d, AttendanceCode.X)] for d in own if d not in pinned)
        goal = target(inp, uid)
        under = model.new_int_var(0, len(inp.days), f"monthly_off_under_{uid}")
        over = model.new_int_var(0, len(inp.days), f"monthly_off_over_{uid}")
        model.add(chosen + under - over == goal)
        for slack, direction in ((under, "shortfall"), (over, "excess")):
            registry.register(
                slack,
                rule=f"monthly_off_{direction}",
                user_id=uid,
                message=f"User {uid}: monthly ordinary X {direction} (target {goal})",
                params={"target": goal},
            )
        for days in ahead:
            cap = entitlement(days, pinned)
            extra = model.new_int_var(0, len(days), f"carry_off_over_{uid}_{days[0]}")
            model.add(
                sum(x[(uid, d, AttendanceCode.X)] for d in days if d not in pinned)
                - extra
                <= cap
            )
            registry.register(
                extra,
                rule="monthly_off_excess",
                user_id=uid,
                day=days[0],
                message=f"User {uid}: ordinary X excess on the carry days (at most {cap})",
                key=CARRY_KEY,
                params={"target": cap},
            )
