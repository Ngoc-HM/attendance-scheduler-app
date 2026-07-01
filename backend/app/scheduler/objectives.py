"""Soft objectives for the CP-SAT model (spec §5.4 + locked decision #6).

Weighted-sum penalty minimized by the solver (the spec's suggested approach).
``add_all`` collects penalty terms from the objective_* modules plus one local
shaping term, and the engine registers the final ``Minimize`` together with
the slack penalties (which dwarf everything here — see ``slack_registry``).

Role-aware priority order (owner decision 2026-06-26):
    cross-people A/D balance (100)  >  premium-off fairness (30)
                                    >  ad_usage (1000/use, but rare)

Balance is CROSS-PEOPLE only — minimise the spread of A and of D across role-A
people (§5.4 #7) — NOT per-person A≈D, which is impossible under the HARD
§5.3 #4 rule "2 pairs → 1 A + 2 D" (it structurally forces more D than A).
Balance and AD-usage apply to ROLE-A people only — role T (AD) and M (O/D)
have no A/D var in their domain.

Off-day placement (two separate concerns):
    - ``premium_off`` (30): fairness of WHO gets the valued Sat/Sun/holiday off,
      rotated evenly across people. Sat/Sun are ordinary working days — offs are
      NOT forced onto the weekend (owner decision 2026-06-18).
    - ``off_pairing`` (15): §5.4 #8 (revived 2026-07-01) prefers each person's two
      weekly offs to be ADJACENT (rest two days in a row), but WITHOUT any weekend
      bias — it only rewards adjacency, never a specific day. Low weight so it
      yields to staffing, comp days and balance.

Shaping terms:
    - ``ad_usage`` (1000/use): A/D is a last resort (§5.3 #6 "bất đắc dĩ") —
      preferred over an uncovered shift (slack 10000) but over nothing else.
      Role-A only (A_D var exists only in the role-A domain).
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler import (
    objective_balance,
    objective_off_pairing,
    objective_premium_off,
)
from app.scheduler.domain import SolverInput

# Relative weights — cross-people A/D balance is the top priority (§5.4 #7).
WEIGHTS = {
    "balance_shifts": 100,       # §5.4 #7 cross-spread
    "premium_off": 30,           # decision #6 — also rotates weekend/holiday offs
    "off_pairing": 15,           # §5.4 #8 — pair the 2 weekly offs adjacently (no weekend bias)
    "ad_usage": 1_000,           # §5.3 #6 — discourage the double shift
}


def add_all(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExpr]:
    """Build and return all soft penalty terms (engine adds the Minimize)."""
    penalties: list[cp_model.LinearExpr] = []
    penalties += objective_balance.terms(model, x, inp, WEIGHTS["balance_shifts"])
    penalties += objective_premium_off.terms(model, x, inp, WEIGHTS["premium_off"])
    penalties += objective_off_pairing.terms(model, x, inp, WEIGHTS["off_pairing"])
    penalties += _ad_usage_terms(x, inp)
    return penalties


def _ad_usage_terms(
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExpr]:
    """Penalize every A/D double shift — legal but last-resort (§5.3 #6).

    Only role-A people have an A/D (A_D) var; the guard ensures no KeyError
    for role-T or role-M people who don't have that var in their domain.
    """
    weight = WEIGHTS["ad_usage"]
    return [
        weight * x[(p.user_id, d, AttendanceCode.A_D)]
        for p in inp.people
        if p.role is Role.A
        for d in inp.days
    ]
