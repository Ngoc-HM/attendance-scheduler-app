"""Days off per month = the month's Saturdays and Sundays (owner 2026-11-10).

The owner's paper roster (July 2026, "TTL 23 WORKING DAYS") gives every
person exactly as many X as the month has Saturdays and Sundays — whatever
the role, leave included. So each person's target is

    W − (their pinned approved-leave days on a Sat/Sun), floored at 0

where W counts the month's Saturdays and Sundays (July 2026: 8, November
2026: 9). Public holidays do not change W: they stay working days that earn
a comp day (decision #5). A leave day on a weekday leaves the target alone.

|chosen X − target| is penalised in both directions. It is an objective,
not a slack and not a violation: the rest rules (at most 5 working days per
Mon–Sun week, ``constraints_weekly_rest``; no more than 5 in a row,
``constraints_consecutive``, owner 2026-11-12) only set a floor, so this
target is what sets how many days off a person gets; a rule's slack can
still push a person above it when their rhythm needs it. Only X the engine
CHOOSES counts (ruling R2: pinned leave is excluded); a CD is not an X.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput

WEEKEND = (5, 6)  # date.weekday(): Saturday, Sunday


def target(inp: SolverInput, user_id: int) -> int:
    """The person's X target for the month (see the module docstring)."""
    weekend_days = sum(1 for d in inp.days if d.weekday() in WEEKEND)
    pinned = inp.approved_off.get(user_id, {})
    pinned_weekend = sum(1 for d in pinned if d in inp.days and d.weekday() in WEEKEND)
    return max(0, weekend_days - pinned_weekend)


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    n_days = len(inp.days)
    penalties: list[cp_model.LinearExpr] = []
    for p in inp.people:
        pinned = inp.approved_off.get(p.user_id, {})
        chosen = sum(x[(p.user_id, d, AttendanceCode.X)] for d in inp.days if d not in pinned)
        gap = model.new_int_var(0, n_days, f"off_target_gap_{p.user_id}")
        model.add_abs_equality(gap, chosen - target(inp, p.user_id))
        penalties.append(weight * gap)
    return penalties
