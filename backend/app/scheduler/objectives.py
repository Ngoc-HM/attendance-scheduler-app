"""Soft objectives for the CP-SAT model (spec §5.4 + locked decision #6).

Weighted-sum penalty minimized by the solver (the spec's suggested approach).
``add_all`` collects the penalty terms of the objective_* modules; the engine
minimises them in phase 2, after the slack of every rule has been minimised
on its own in phase 1 (decision #45) — so no soft term can buy a violation.

A/D duties (role A only, owner 2026-06-26 / 2026-07-22):
    - ``individual_shift_gap`` (300): each A person's own |A − D|.
    - ``balance_shifts`` (100): spread of A and of D totals across group A.
Emergency A/D is never generated. These do not apply to T/F/M.

Month end (real-data run 2026-11-12, soft, never reported):
    - ``boundary_week`` (3000 per rest day group A would owe next month
      beyond what next month's first days can absorb): when the last
      Mon–Sun week runs into next month, rule W only caps this month's part
      of it; without a look-ahead December 2026 left every group-A person 4
      worked days in the week of 28 Dec and January could not staff 1–2
      January.

Reserve (owner 2026-11-12, soft, never reported):
    - ``reserve_cover`` (300 per person missing): on every flight day
      min(3, size of group A) role-A people at work — one in reserve above
      the staffing floor (1A+1D for one pair; two pairs already need 3).

Days off (owner 2026-11-10 / 2026-11-12 — the 7-day blocks and the rolling
"2 rest days in any 7" reading are gone; the rest rules are "at most 5
working days per Mon–Sun week" and "no more than 5 in a row", the 2 rest
days of a week need not be adjacent; these terms shape the rest):
    - ``monthly_off_target`` (1000 per day): chosen X per person = the month's
      Saturdays + Sundays, minus their approved leave on those days (the
      owner's paper roster: 8 X in July 2026 for everyone). This is what sets
      how many days off a person gets.
    - ``group_cover`` (200): a role group (same role, 2+ people) is never all
      off on the same day.
    - ``pair_points_fair`` (60 per point): reward on the LOWEST running total
      of weekday-bonus points in a role group — history (carry of the 12
      months before, capped at 24 above the group's lowest) + this month — so
      the good pairs are taken in turns, with memory. The reward runs down
      the ranking: the second lowest total earns half (30), the third a
      quarter (15), the highest nothing, so whoever is behind at ANY rank comes
      before whoever is ahead (live run 2026-11-12: with the lowest member
      capped, the leader kept taking Fri+Sat from the one in the middle).
      ``pair_points_spread`` (5 per point of max − min of the running
      totals) breaks the ties that leaves open.
    - ``premium_off`` (30): fair share of Sat/Sun/holiday X, with carry
      across months (decision #6).
    - ``off_pairing`` (15 per point): 1 point per X next to another X (2 per
      pair), plus Fri+Sat +3 / Sat+Sun +2 / Sun+Mon +1.

Why these numbers — what ONE X more or less than the target can gain on
every other soft term, everything else fixed:
    - one X MORE: pairing — the X is paired (+1), pairs two lone neighbours
      (+2) and between X on Fri and Sun adds Fri+Sat and Sat+Sun (+3 +2):
      8 x 15 = 120; the lowest running total +5 → 5 x 60 = 300 (the rank
      weights only fall from there, so no other rank gains more); one premium
      day → 30; for group A an even working count closes the |A − D| gap by
      1 → 300 and the A or D spread by 1 → 100. Total 850. An extra X never
      removes an all-off day, so ``group_cover`` gains nothing.
    - one X FEWER: one all-off day less → 200, one reserve person more on a
      flight day → 300, premium 30, A/D 300 + 100, and the leader of a
      group losing a bonus pair narrows the spread tie-break (below) by up
      to 5 x 5 = 25; the other pair terms can only lose. Total 955. An
      extra X never adds a reserve person.
    ``monthly_off_target`` = 1000 > 955 (and > 875 for one X more, spread
      tie-break included), so nobody gets a free day off, or loses one, for
      the reserve, balance or preferences.
    - ``reserve_cover`` 300: above the most a member furthest behind gains
      from a Fri+Sat instead of a weekday pair (3 points x (15 + 60 + 5) =
      240) — the reserve on a one-pair Friday comes before the favourite
      pair — and above ``group_cover``; below the target (above) and the
      rule slack, so the reserve never costs anyone a day off or buys a
      violation. It equals the A/D gap weight: working days are fixed by the
      target, so the two rarely meet, and the gap still decides A or D.
    - ``boundary_week`` 3000 > ``monthly_off_target`` 1000 (and > the 955 a
      day off less can gain elsewhere): leaving next month an impossible
      start costs more than one extra day off now, so a group-A person takes
      a rest day in the last days of the month (9 X instead of 8) when the
      week would otherwise break next month. Below the rule slack (10 000):
      it never buys a violation of this month. Above the comp-day slack
      (2 000), but it can never profit from one: an unearned CD is rest
      that an extra X (1000) gives cheaper, and withholding an owed CD only
      adds work. The two-phase solve fixes all slack first anyway.
    - ``monthly_off_target`` stays below the comp-day slack (2 000) and the rule slack (10 000):
      a rest rule or an owed CD always wins over the target. The two-phase
      solve fixes the slack first anyway (decision #45); in the single
      combined fallback ten days of deviation would equal one slack unit.
    - ``pair_points_fair`` 60: one Fri+Sat handed to the member furthest
      behind is worth 3 x 60 = 180, more than what the leader's own pairing
      reward loses with it (5 points x 15 = 75) plus a pair broken elsewhere
      to make room (2 base points x 15 = 30), so the turn is taken. The
      owner's prototype on real data (Dec 2026 – Feb 2027, 4 A / 3 F / 2 M)
      kept every month target and converged the running totals (group A
      19/17/17/17). It stays below ``group_cover`` per pair-sized step: a
      Fri+Sat for a third member (3 x 60 + 5 x 15 = 255) never pays for the
      two days the whole group would then be off (2 x 200 = 400).
    - ``pair_points_spread`` 5 < ``off_pairing`` 15 per point: taking a
      bonus away from the top without giving it to anyone saves 5 per point
      of spread but loses 15 per point of pairing, so it never levels down;
      it only decides who of equals gets the pair. With it, one extra X can
      gain at most 5 x 5 = 25 more: 875 < 1000 still.
    - ``group_cover`` (200) > the pair rewards a third member could gain by
      also taking Fri+Sat, but below the A/D gap (300): flight staffing
      already keeps group A at work.
    - Pair rewards per point (15 + 60 + 5 = 80) stay below the A/D balance
      terms (100, 300) per point, so the day-off preferences never unbalance
      group A's duties.

Only X the engine CHOOSES counts in ``monthly_off_target``, ``premium_off``
and the pair bonus (ruling R2): approved leave is not a perk.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import (
    objective_balance,
    objective_boundary_week,
    objective_group_cover,
    objective_monthly_off_target,
    objective_off_pairing,
    objective_pair_points_fair,
    objective_premium_off,
    objective_reserve_cover,
)
from app.scheduler.domain import SolverInput

# Relative weights within the soft scheduling objectives (reasons above).
WEIGHTS = {
    "boundary_week": 3000,       # owner data 2026-11-12 — leave next month a startable week
    "individual_shift_gap": 300, # owner 2026-07-22 — each A person: A ~= D
    "balance_shifts": 100,       # §5.4 #7 cross-spread of A and D
    "monthly_off_target": 1000,  # owner 2026-11-10 — per day off the Sat+Sun count
    "reserve_cover": 300,        # owner 2026-11-12 — 3 group-A at work on flight days
    "group_cover": 200,          # owner 2026-11-10 — a role group never all off
    "pair_points_fair": 60,      # owner 2026-11-12 — good pairs in turns, with memory
    "pair_points_spread": 5,     # tie-break of the turns: the top yields, never levels down
    "premium_off": 30,           # decision #6 — Sat/Sun/holiday X shared, with carry
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
    penalties += objective_boundary_week.terms(model, x, inp, WEIGHTS["boundary_week"])
    penalties += objective_group_cover.terms(model, x, inp, WEIGHTS["group_cover"])
    penalties += objective_reserve_cover.terms(model, x, inp, WEIGHTS["reserve_cover"])
    penalties += objective_monthly_off_target.terms(
        model, x, inp, WEIGHTS["monthly_off_target"]
    )
    penalties += objective_premium_off.terms(model, x, inp, WEIGHTS["premium_off"])
    pairs = objective_off_pairing.bonus_pairs(model, x, inp)
    penalties += objective_off_pairing.terms(model, x, inp, pairs, WEIGHTS["off_pairing"])
    penalties += objective_pair_points_fair.terms(
        model, pairs, inp, WEIGHTS["pair_points_fair"], WEIGHTS["pair_points_spread"]
    )
    return penalties
