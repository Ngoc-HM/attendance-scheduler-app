"""Soft objectives for the CP-SAT model (spec §5.4 + locked decision #6).

Weighted-sum penalty minimized by the solver (the spec's suggested approach).
``add_all`` collects penalty terms from the objective_* modules plus one local
shaping term, and the engine registers the final ``Minimize`` together with
the slack penalties (which dwarf everything here — see ``slack_registry``).

Role-aware priority order (owner decision 2026-06-26):
    per-person A≈D gap (300) > cross-people A-versus-D balance (100)
                            > premium-off fairness (30)

Balance has two parts for role-A people: minimize the spread of A and D duties
across the group, and minimize each person's own ``|A total - D total|``.
Flight demand remains authoritative, so a 2-pair month can still structurally
contain more D than A. Automatic scheduling never creates emergency A/D.
These objectives do not apply to T/F/M role domains.

Off-day placement (two separate concerns):
    - ``premium_off`` (30): fairness of WHO gets the valued Sat/Sun/holiday off,
      rotated evenly across people. Sat/Sun are ordinary working days — offs are
      NOT forced onto the weekend (owner decision 2026-06-18).
    - ``off_pairing`` (15): §5.4 #8 (revived 2026-07-01) prefers each person's two
      weekly offs to be ADJACENT (rest two days in a row), but WITHOUT any weekend
      bias — it only rewards adjacency, never a specific day. Low weight so it
      yields to staffing, comp days and balance.
    - ``tail_off`` (500): the leftover days after the 28th have no off quota
      (owner 2026-11-10); each X the engine chooses there is penalised so they
      stay ordinary working days unless a rest rule needs a day off.

"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import (
    objective_balance,
    objective_off_pairing,
    objective_premium_off,
    objective_tail_off,
)
from app.scheduler.domain import SolverInput

# Relative weights within the soft scheduling objectives.
WEIGHTS = {
    "balance_shifts": 100,       # §5.4 #7 cross-spread
    "individual_shift_gap": 300, # owner 2026-07-22 — each A person: A ~= D
    "premium_off": 30,           # decision #6 — also rotates weekend/holiday offs
    "off_pairing": 15,           # §5.4 #8 — pair the 2 weekly offs adjacently (no weekend bias)
    # Owner 2026-11-10 — per X chosen on a leftover day (29–end). One such X
    # removes one working cell, which can improve the other terms by at most
    # 300 (own A~D gap) + 100 (A or D spread) + 30 (premium-off spread) = 430,
    # so 500 means a leftover-day X is never bought for balance or fairness.
    # It stays far below the comp-day slack (2 000) and SLACK_WEIGHT (10 000),
    # so a rest rule always wins; a whole tail stays below one SLACK_WEIGHT
    # while people x leftover days < 20 (6 people in a 31-day month, 9 in a
    # 30-day one). Larger rosters only matter in the single combined fallback
    # solve: the normal two-phase solve fixes the slack first (decision #45).
    "tail_off": 500,
}


def add_all(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExpr]:
    """Build and return all soft penalty terms (engine adds the Minimize)."""
    penalties: list[cp_model.LinearExpr] = []
    penalties += objective_balance.terms(model, x, inp, WEIGHTS["balance_shifts"])
    penalties += objective_balance.individual_terms(
        model, x, inp, WEIGHTS["individual_shift_gap"]
    )
    penalties += objective_premium_off.terms(model, x, inp, WEIGHTS["premium_off"])
    penalties += objective_off_pairing.terms(model, x, inp, WEIGHTS["off_pairing"])
    penalties += objective_tail_off.terms(model, x, inp, WEIGHTS["tail_off"])
    return penalties
