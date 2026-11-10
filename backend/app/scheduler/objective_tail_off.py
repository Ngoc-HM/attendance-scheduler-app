"""Leftover days of the month are ordinary working days (owner 2026-11-10).

The days after the 28th form a partial block with NO off-day quota
(``calendar_utils.block_off_target``). Without a quota the solver would be
indifferent there for roles with no staffing floor (F, M, T) and could hand
out free days off. This term counts every X the engine CHOOSES on those days
and the solver minimises it.

It is an objective, not a slack: a day off there that max-5-consecutive or
the rolling-7-day rest rule requires is legitimate and is never reported as
a violation — it only costs this small penalty, which the slack (10 000 per
unit) always outweighs.

Pinned approved leave (an X in the decision layer) is not chosen and is not
counted — the same rule as ``objective_premium_off`` (ruling R2).
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.calendar_utils import partial_block_days
from app.scheduler.domain import SolverInput


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    tail = partial_block_days(inp.weeks)
    if not tail:
        return []  # e.g. February in a common year: 4 full blocks
    chosen = [
        x[(p.user_id, d, AttendanceCode.X)]
        for p in inp.people
        for d in tail
        if d not in inp.approved_off.get(p.user_id, {})
    ]
    if not chosen:
        return []
    return [weight * cp_model.LinearExpr.sum(chosen)]
