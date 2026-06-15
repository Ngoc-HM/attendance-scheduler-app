"""§5.4 #8 — prefer the two weekly OFF days adjacent, weekend first (soft).

Preference order for an adjacent OFF pair (spec §5 / §6):
    1. Sat + Sun   (best — reward 3)
    2. Fri + Sat   (reward 2)
    3. Sun + Mon   (reward 1)

For every adjacent calendar pair of those shapes in the month, an indicator
bool is true iff BOTH days are X; rewards enter the minimized objective as
negative penalties. Pairs are calendar-based on purpose: a Sat+Sun pair may
straddle two 7-day blocks (decision #7) and should still be rewarded.
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput

# (weekday of first day, reward multiplier); weekday(): Mon=0 .. Sun=6.
PAIR_REWARDS: tuple[tuple[int, int], ...] = (
    (5, 3),  # Sat+Sun
    (4, 2),  # Fri+Sat
    (6, 1),  # Sun+Mon
)


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    day_set = set(inp.days)
    penalties: list[cp_model.LinearExpr] = []

    for p in inp.people:
        for d in sorted(inp.days):
            nxt = d + timedelta(days=1)
            if nxt not in day_set:
                continue
            for first_weekday, reward in PAIR_REWARDS:
                if d.weekday() != first_weekday:
                    continue
                pair = model.NewBoolVar(
                    f"pair_{p.user_id}_{d.isoformat()}_{first_weekday}"
                )
                both = [
                    x[(p.user_id, d, AttendanceCode.X)],
                    x[(p.user_id, nxt, AttendanceCode.X)],
                ]
                # pair <=> AND(both X)
                model.AddBoolAnd(both).OnlyEnforceIf(pair)
                model.AddBoolOr([b.Not() for b in both]).OnlyEnforceIf(pair.Not())
                # Reward = negative penalty in the minimized objective.
                penalties.append(-weight * reward * pair)

    return penalties
