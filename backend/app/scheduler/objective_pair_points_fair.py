"""Good day-off pairs are shared out fairly (owner 2026-11-10).

Owner: "… đảm bảo không tị nạnh ai". Per role group (``role_groups``), the
LOWEST total of this month's weekday-bonus points (``objective_off_pairing``)
earns a reward per point, so the solver lifts whoever got the worst pairs
first — nobody keeps only Sun+Mon while colleagues take every Fri+Sat.

Max-min, not a spread: penalising (max − min) was tried and levels DOWN —
on a probe with 3 F and 2 M it gave everybody Tue+Wed / Thu+Fri pairs (zero
bonus, zero spread) instead of sharing the good ones. A reward on the minimum
never makes a better pair for someone a cost. Across months, the existing premium-off
fairness (``objective_premium_off``, with its carry) still balances who was
off on Sat/Sun/holidays.
"""

from __future__ import annotations

from ortools.sat.python import cp_model

from app.scheduler.domain import SolverInput
from app.scheduler.objective_off_pairing import BonusPair
from app.scheduler.role_codes import role_groups


def terms(
    model: cp_model.CpModel,
    found: list[BonusPair],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    penalties: list[cp_model.LinearExpr] = []
    for group in role_groups(inp.people):
        role = group[0].role.value
        totals: list[cp_model.IntVar] = []
        bound = 0
        for p in group:
            own = [pair for pair in found if pair.user_id == p.user_id]
            top = sum(pair.bonus for pair in own)
            bound = max(bound, top)
            total = model.new_int_var(0, top, f"pair_points_{p.user_id}")
            model.add(total == sum(pair.bonus * pair.var for pair in own))
            totals.append(total)
        lo = model.new_int_var(0, bound, f"pair_points_min_{role}")
        model.add_min_equality(lo, totals)
        penalties.append(-weight * lo)  # reward the least-served member
    return penalties
