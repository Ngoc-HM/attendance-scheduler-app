"""Named objectives, minimized in strict priority order by the engine.

Rule/monthly-quota violations precede these stages. Every role-A individual
A/D gap rank precedes aggregate balance, operational role-group cover,
independent chronological rest turns, and reserve/rest-shaping preferences.
No finite soft weight can purchase a higher-priority regression.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import (
    objective_balance,
    objective_boundary_week,
    objective_group_cover,
    objective_off_pairing,
    objective_pair_points_fair,
    objective_premium_off,
    objective_reserve_cover,
    objective_rest_spacing,
)
from app.scheduler.domain import SolverInput

# Only these final, lower-priority preferences share a weighted objective.
WEIGHTS = {
    "reserve_cover": 300,
    "premium_off": 30,
    "off_pairing": 15,
}


def ordered_terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[tuple[str, cp_model.LinearExprT]]:
    stages = [("ordinary_rest_spacing", sum(objective_rest_spacing.terms(model, x, inp)))]
    stages += objective_balance.ordered_terms(model, x, inp)
    # Keep every role group operational before maximizing preferred turns.
    # Otherwise groups without flight demand could all take every weekend.
    cover = objective_group_cover.terms(model, x, inp, 1)
    if cover:
        stages.append(("role_group_cover", sum(cover)))
    lookahead = objective_boundary_week.terms(model, x, inp, 1)
    if lookahead:
        stages.append(("known_next_month_consecutive_cover", sum(lookahead)))
    pairs = objective_off_pairing.bonus_pairs(model, x, inp)
    stages += objective_pair_points_fair.ordered_terms(model, pairs, inp)
    preferences = []
    preferences += objective_reserve_cover.terms(model, x, inp, WEIGHTS["reserve_cover"])
    preferences += objective_premium_off.terms(model, x, inp, WEIGHTS["premium_off"])
    preferences += objective_off_pairing.terms(model, x, inp, pairs, WEIGHTS["off_pairing"])
    stages.append(("reserve_and_rest_preferences", sum(preferences)))
    return stages


def add_all(model, x, inp) -> list[cp_model.LinearExprT]:
    """Compatibility builder; engine uses ordered_terms to preserve priority."""
    return [expression for _, expression in ordered_terms(model, x, inp)]
