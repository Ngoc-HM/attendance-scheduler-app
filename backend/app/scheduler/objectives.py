"""Soft objectives for the CP-SAT model (spec §5.4 + locked decision #6).

Weighted-sum penalty minimized by the solver (the spec's suggested approach).
``add_all`` collects penalty terms from the objective_* modules plus two local
shaping terms, and the engine registers the final ``Minimize`` together with
the slack penalties (which dwarf everything here — see ``slack_registry``).

Priority order (spec §5.4 note + owner decisions):
    balance A/D (100)  >  premium-off fairness (30)

Weekend pairing was removed (owner decision 2026-06-18): Sat/Sun/holiday are
ordinary working days, so the two weekly OFF days must NOT be forced onto the
weekend. Fairness of who gets the (still-valued) weekend/holiday OFF is handled
by ``premium_off`` alone, which spreads those premium offs evenly across people
(the rotation the owner asked for — "this week off Sat/Sun → next week works").

Shaping terms:
    - ``ad_usage`` (1000/use): A/D is a last resort (§5.3 #6 "bất đắc dĩ") —
      preferred over an uncovered shift (slack 10000) but over nothing else.

(O/D is no longer auto-assigned, so the old ``nonfixed_flight_duty`` term that
steered M/T to office duty was removed — every role now takes A/D flight shifts,
matching the manual roster WR JUN26.)

Conflict priority (§5.4 #9, weight 5) is resolved at leave-approval time
(phase 03 ``leave_conflict_resolver``), not inside the solver.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import objective_balance, objective_premium_off
from app.scheduler.domain import SolverInput

# Relative weights — balance is the top priority (§5.4 note).
WEIGHTS = {
    "balance_shifts": 100,       # §5.4 #7
    "premium_off": 30,           # decision #6 — also rotates weekend/holiday offs
    "ad_usage": 1_000,           # §5.3 #6 — discourage the double shift
}


def add_all(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    assignable_codes: tuple[AttendanceCode, ...],
) -> list[cp_model.LinearExpr]:
    """Build and return all soft penalty terms (engine adds the Minimize)."""
    penalties: list[cp_model.LinearExpr] = []
    penalties += objective_balance.terms(model, x, inp, WEIGHTS["balance_shifts"])
    penalties += objective_premium_off.terms(model, x, inp, WEIGHTS["premium_off"])
    penalties += _ad_usage_terms(x, inp)
    return penalties


def _ad_usage_terms(
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExpr]:
    """Penalize every A/D double shift — legal but last-resort (§5.3 #6)."""
    weight = WEIGHTS["ad_usage"]
    return [
        weight * x[(p.user_id, d, AttendanceCode.A_D)]
        for p in inp.people
        for d in inp.days
    ]
