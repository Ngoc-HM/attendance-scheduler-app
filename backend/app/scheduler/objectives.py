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

"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import (
    objective_balance,
    objective_off_pairing,
    objective_premium_off,
)
from app.scheduler.domain import SolverInput

# Relative weights within the soft scheduling objectives.
WEIGHTS = {
    "balance_shifts": 100,       # §5.4 #7 cross-spread
    "individual_shift_gap": 300, # owner 2026-07-22 — each A person: A ~= D
    "premium_off": 30,           # decision #6 — also rotates weekend/holiday offs
    "off_pairing": 15,           # §5.4 #8 — pair the 2 weekly offs adjacently (no weekend bias)
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
    return penalties
