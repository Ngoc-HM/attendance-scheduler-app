"""Soft objectives for the CP-SAT model (spec §5.4 + locked decision #6).

Weighted-sum penalty minimized by the solver (the spec's suggested approach).
``add_all`` collects the penalty terms of the objective_* modules; the engine
minimises them in phase 2, after the slack of every rule has been minimised
on its own in phase 1 (decision #45) — so no soft term can buy a violation.

A/D duties (role A only, owner 2026-06-26 / 2026-07-22):
    - ``individual_shift_gap`` (300): each A person's own |A − D|.
    - ``balance_shifts`` (100): spread of A and of D totals across group A.
Emergency A/D is never generated. These do not apply to T/F/M.

Days off (owner 2026-11-10 — the 7-day blocks are gone; "at most 5 working
days in any 7" is the only binding rest rule; these terms shape the rest):
    - ``monthly_off_target`` (1000 per day): chosen X per person = the month's
      Saturdays + Sundays, minus their approved leave on those days (the
      owner's paper roster: 8 X in July 2026 for everyone).
    - ``group_cover`` (200): a role group (same role, 2+ people) is never all
      off on the same day.
    - ``premium_off`` (30): fair share of Sat/Sun/holiday X, with carry
      across months (decision #6).
    - ``pair_points_fair`` (20): reward per weekday-bonus point of the
      least-served member of a role group (max-min; a spread levelled down).
    - ``off_pairing`` (15 per point): 1 point per X next to another X (2 per
      pair), plus Fri+Sat +3 / Sat+Sun +2 / Sun+Mon +1.

Why these numbers — what ONE X more or less than the target can gain on
every other soft term, everything else fixed:
    - pairing: the X is paired (+1), pairs two lone neighbours (+2) and
      between X on Fri and Sun adds Fri+Sat and Sat+Sun (+3 +2): 8 x 15 =
      120; the least-served member's bonus +5 → 5 x 20 = 100; one premium
      day → 30; one day the group is no longer all off → 200; for group A
      an even working count closes the |A − D| gap by 1 → 300 and the A or D
      spread by 1 → 100. Total 850. ``monthly_off_target`` = 1000 > 850, so
      nobody gets a free day off, or loses one, for balance or preferences.
    - It stays below the comp-day slack (2 000) and the rule slack (10 000):
      a rest rule or an owed CD always wins over the target. The two-phase
      solve fixes the slack first anyway (decision #45); in the single
      combined fallback ten days of deviation would equal one slack unit.
    - ``group_cover`` (200) > the pair rewards a third member could gain by
      also taking Fri+Sat (2 all-off days cost 400 against ~75), but below
      the A/D gap (300): flight staffing already keeps group A at work.
    - Pair rewards and their fairness (15/point, 20) stay below the A/D
      balance terms (100, 300) per point, so the day-off preferences never
      unbalance group A's duties.

Only X the engine CHOOSES counts in ``monthly_off_target``, ``premium_off``
and the pair bonus (ruling R2): approved leave is not a perk.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import (
    objective_balance,
    objective_group_cover,
    objective_monthly_off_target,
    objective_off_pairing,
    objective_pair_points_fair,
    objective_premium_off,
)
from app.scheduler.domain import SolverInput

# Relative weights within the soft scheduling objectives (reasons above).
WEIGHTS = {
    "individual_shift_gap": 300, # owner 2026-07-22 — each A person: A ~= D
    "balance_shifts": 100,       # §5.4 #7 cross-spread of A and D
    "monthly_off_target": 1000,  # owner 2026-11-10 — per day off the Sat+Sun count
    "group_cover": 200,          # owner 2026-11-10 — a role group never all off
    "premium_off": 30,           # decision #6 — Sat/Sun/holiday X shared, with carry
    "pair_points_fair": 20,      # owner 2026-11-10 — good pairs taken in turns
    "off_pairing": 15,           # owner 2026-11-10 — per point: 2/pair + weekday bonus
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
    penalties += objective_group_cover.terms(model, x, inp, WEIGHTS["group_cover"])
    penalties += objective_monthly_off_target.terms(
        model, x, inp, WEIGHTS["monthly_off_target"]
    )
    penalties += objective_premium_off.terms(model, x, inp, WEIGHTS["premium_off"])
    pairs = objective_off_pairing.bonus_pairs(model, x, inp)
    penalties += objective_off_pairing.terms(model, x, inp, pairs, WEIGHTS["off_pairing"])
    penalties += objective_pair_points_fair.terms(
        model, pairs, inp, WEIGHTS["pair_points_fair"]
    )
    return penalties
