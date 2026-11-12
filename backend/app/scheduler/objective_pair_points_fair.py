"""Good day-off pairs taken in turns, with memory (owner 2026-11-10 / 11-12).

Owner: "Khung thứ 6, 7 nghỉ sẽ phải nhường cho người khác … cảm giác nó chưa
công bằng." Per role group (``role_groups``), each member has a RUNNING
TOTAL of weekday-bonus points (``objective_off_pairing``: Fri+Sat 3,
Sat+Sun 2, Sun+Mon 1):

    running = min(CAP, carry − the group's lowest carry) + this month's points

where ``carry`` is ``PersonInput.carry_pair_points`` (the points of the 12
months before, from the effective history). The LOWEST running total of the
group earns a reward per point, so whoever is behind gets the good pairs
first and whoever has had the most yields them.

Only the difference to the group's lowest carry matters, so a group with
equal history competes on this month alone. ``CAP`` keeps one very old
imbalance from dominating: a member more than CAP points ahead is treated as
exactly CAP ahead, so the others can still catch up in a few months while
that member is not frozen out for a year.

Max-min first, not a spread: penalising (max − min) ALONE was tried and
levels DOWN — on a probe with 3 F and 2 M it gave everybody Tue+Wed /
Thu+Fri pairs (zero bonus, zero spread) instead of sharing the good ones. A
reward on the minimum never makes a better pair for someone a cost.

The minimum alone leaves the top free, though: 3 T over February 2027 got
Fri+Sat 2/4/2 (points 7/12/7) — the lowest cannot rise above 7 with 8
Fri+Sat slots for three people, so nothing stopped one member taking four.
A small spread term (``spread_weight`` per point of max − min) breaks that
tie towards 3/3/2. It cannot level down: taking a pair away without handing
it to someone else loses at least its bonus in ``off_pairing`` (15 per
point), more than the spread saves per point.

Not only the lowest (live run in the app, December 2026, 3 F with carries
5 / 11 / 9): the lowest member was held at 9 by a forced rest day, so the
reward on the minimum was spent, and the member with the MOST history took
three Fri+Sat while the one in the middle got one (running totals
14 / 22 / 14) — the spread tie-break (15 per pair) lost to the other soft
terms. So the reward runs down the whole ranking (leximin): the lowest
running total earns ``weight`` per point, the second lowest half of it, the
third a quarter …, the highest nothing. Whoever is behind — at any rank —
comes before whoever is ahead, and it is still a reward only, so it never
levels down. A group of two is unchanged (lowest ``weight``, highest 0).

The ranking needs no sorting: the sum of the k lowest totals is the largest
value not above the sum of any k members, so one variable per rank bounded
by every k-subset is enough (a first version with a level and a gap variable
per member slowed the single-worker search until a month's X target was
missed). ``DEPTH`` ranks are rewarded, which keeps the subsets few in a
large group.
"""

from __future__ import annotations

from itertools import combinations

from ortools.sat.python import cp_model

from app.scheduler.domain import SolverInput
from app.scheduler.objective_off_pairing import BonusPair
from app.scheduler.role_codes import role_groups

# Largest head start (points) a member's history can give over the group's
# lowest carry — about two months of Fri+Sat pairs (owner 2026-11-12).
CAP = 24
# How many of the lowest ranks of a group are rewarded (60, 30, 15 per point).
DEPTH = 3


def terms(
    model: cp_model.CpModel,
    found: list[BonusPair],
    inp: SolverInput,
    weight: int,
    spread_weight: int,
) -> list[cp_model.LinearExpr]:
    penalties: list[cp_model.LinearExpr] = []
    for group in role_groups(inp.people):
        role = group[0].role.value
        floor = min(p.carry_pair_points for p in group)
        totals: list[cp_model.IntVar] = []
        bound = 0
        for p in group:
            ahead = min(CAP, max(0, p.carry_pair_points - floor))
            own = [pair for pair in found if pair.user_id == p.user_id]
            top = ahead + sum(pair.bonus for pair in own)
            bound = max(bound, top)
            total = model.new_int_var(0, top, f"pair_points_{p.user_id}")
            model.add(total == ahead + sum(pair.bonus * pair.var for pair in own))
            totals.append(total)
        lo = model.new_int_var(0, bound, f"pair_points_min_{role}")
        hi = model.new_int_var(0, bound, f"pair_points_max_{role}")
        model.add_min_equality(lo, totals)
        model.add_max_equality(hi, totals)
        # Rank weights: lowest ``weight``, then halved, the highest 0. A
        # weight w_k on the k-th lowest total equals (w_k − w_k+1) on the
        # sum of the k lowest (module docstring).
        n = len(totals)
        rank = [weight >> k if k < min(n - 1, DEPTH) else 0 for k in range(n)]
        penalties.append(-(rank[0] - rank[1]) * lo)
        for k in range(2, n):
            step = rank[k - 1] - rank[k]
            if not step:
                continue
            lowest = model.new_int_var(0, k * bound, f"pair_points_low{k}_{role}")
            for subset in combinations(totals, k):
                model.add(lowest <= sum(subset))  # maximised: the k lowest
            penalties.append(-step * lowest)
        penalties.append(spread_weight * (hi - lo))  # tie-break: the top yields
    return penalties
