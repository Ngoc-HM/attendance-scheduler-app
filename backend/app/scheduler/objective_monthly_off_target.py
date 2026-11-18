"""Monthly ordinary-X entitlement shared by generation and persisted recheck.

Target = Saturdays and Sundays minus approved leave on those dates, floored
at zero. Weekday approved leave and CD reduce duties in addition to this X
entitlement; holidays retain their existing compensation policy. Diagnostic
constraints enforce the target; ``terms`` remains a compatibility wrapper.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.carried import own_days
from app.scheduler.domain import SolverInput

WEEKEND = (5, 6)  # date.weekday(): Saturday, Sunday


def entitlement(days: list[date], pinned: dict[date, AttendanceCode]) -> int:
    """Ordinary X owed after the existing weekend-leave adjustment."""
    included = set(days)
    return max(
        0,
        sum(d.weekday() in WEEKEND for d in included)
        - sum(d in included and d.weekday() in WEEKEND for d in pinned),
    )


def target(inp: SolverInput, user_id: int) -> int:
    """The person's X target for the window's own month (see the module
    docstring); the carry days after it have their own bound."""
    return entitlement(own_days(inp), inp.approved_off.get(user_id, {}))


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    days = own_days(inp)
    n_days = len(days)
    penalties: list[cp_model.LinearExpr] = []
    for p in inp.people:
        pinned = inp.approved_off.get(p.user_id, {})
        chosen = sum(x[(p.user_id, d, AttendanceCode.X)] for d in days if d not in pinned)
        gap = model.new_int_var(0, n_days, f"off_target_gap_{p.user_id}")
        model.add_abs_equality(gap, chosen - target(inp, p.user_id))
        penalties.append(weight * gap)
    return penalties
