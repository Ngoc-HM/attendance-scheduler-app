"""Soft objectives for the CP-SAT model (spec §5.4 + locked decision #6).

Weighted-sum penalty minimized by the solver (the spec's suggested approach).
``add_all`` collects penalty terms from the objective_* modules plus two local
shaping terms, and the engine registers the final ``Minimize`` together with
the slack penalties (which dwarf everything here — see ``slack_registry``).

Priority order (spec §5.4 note + owner decisions):
    balance A/D (100)  >  premium-off fairness (30)  >  weekend pairing (10)

Shaping terms:
    - ``ad_usage`` (1000/use): A/D is a last resort (§5.3 #6 "bất đắc dĩ") —
      preferred over an uncovered shift (slack 10000) but over nothing else.
    - ``nonfixed_flight_duty`` (1/use): nudges flexible roles (M/T) to O/D on
      working days; only the fixed group takes flight shifts by default.

Conflict priority (§5.4 #9, weight 5) is resolved at leave-approval time
(phase 03 ``leave_conflict_resolver``), not inside the solver.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import objective_balance, objective_premium_off, objective_weekend
from app.scheduler.domain import SolverInput

# Relative weights — balance is the top priority (§5.4 note).
WEIGHTS = {
    "balance_shifts": 100,       # §5.4 #7
    "premium_off": 30,           # decision #6
    "weekend_pairing": 10,       # §5.4 #8
    "ad_usage": 1_000,           # §5.3 #6 — discourage the double shift
    "nonfixed_flight_duty": 1,   # decision #3 — M/T default to O/D
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
    penalties += objective_weekend.terms(model, x, inp, WEIGHTS["weekend_pairing"])
    penalties += _ad_usage_terms(x, inp)
    penalties += _nonfixed_flight_duty_terms(x, inp)
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


def _nonfixed_flight_duty_terms(
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExpr]:
    """Tiny penalty steering flexible roles (M/T) to O/D over flight codes."""
    weight = WEIGHTS["nonfixed_flight_duty"]
    flight_codes = (AttendanceCode.A, AttendanceCode.D)
    return [
        weight * x[(p.user_id, d, c)]
        for p in inp.people
        if not p.role.is_fixed
        for d in inp.days
        for c in flight_codes
    ]
