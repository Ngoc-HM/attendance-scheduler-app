"""Soft objectives for the CP-SAT model (spec §5.4).

Implemented as a weighted-sum penalty that the solver minimizes (spec's
suggested approach). ``add_all`` collects penalty terms from each builder and
registers the objective. Balance of A/D shifts carries the highest weight
(§5.4 note).
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput

# Relative weights — balance is the top priority (§5.4 note).
WEIGHTS = {
    "balance_shifts": 100,  # §5.4 #7
    "weekend_pairing": 10,  # §5.4 #8
    "conflict_priority": 5,  # §5.4 #9
}


def add_all(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    assignable_codes: tuple[AttendanceCode, ...],
) -> None:
    penalties: list[cp_model.LinearExpr] = []
    penalties += balance_shifts(model, x, inp)
    penalties += weekend_pairing(model, x, inp)

    if penalties:
        model.Minimize(sum(penalties))


def balance_shifts(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExpr]:
    """§5.4 #7 — minimize the spread of A counts (and of D counts) across
    people (especially A1–A4).

    TODO: per person create int totals ``sum(A over month)`` and ``sum(D)``;
    introduce max/min vars and penalize ``(maxA-minA) + (maxD-minD)`` weighted
    by ``WEIGHTS['balance_shifts']``. Returns the weighted penalty terms.
    """
    return []  # TODO


def weekend_pairing(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExpr]:
    """§5.4 #8 — prefer the two weekly OFF days adjacent, in order:
    (1) Sat+Sun, (2) Fri+Sat, (3) Sun+Mon.

    TODO: reward/penalize based on whether the week's two X days form one of
    the preferred adjacent pairs, weighted by ``WEIGHTS['weekend_pairing']``.
    """
    return []  # TODO
