"""Independent chronological preferred-rest turns, within each role.

Stages visit Fri+Sat dates first, then Sat+Sun, then Sun+Mon. At each date,
priority uses genuine same-kind awards BEFORE it: fewer awards, then the
oldest last award. Earlier decisions in this solve participate in both.
Positive rank rewards prevent the empty-award degeneracy. Higher priorities
(staffing, entitlement and A/D fairness) remain fixed by the engine.
"""

from __future__ import annotations

from ortools.sat.python import cp_model

from app.scheduler.domain import RestTurnHistory, SolverInput
from app.scheduler.objective_off_pairing import BonusPair

KINDS = ((4, "fri_sat"), (5, "sat_sun"), (6, "sun_mon"))


def ordered_terms(
    model: cp_model.CpModel,
    found: list[BonusPair],
    inp: SolverInput,
) -> list[tuple[str, cp_model.LinearExprT]]:
    """Minimised per-date stages; no later award can purchase a skipped turn.

    Each candidate's rank is the number of eligible peers who do NOT outrank
    it (ties included). A base larger than all candidates makes one better
    rank worth more than every lower rank together. All ranks earn a positive
    reward, so feasible awards are never suppressed merely to avoid bypasses.
    Large groups use separate rank stages if that encoding would overflow
    CP-SAT integers; every rank participates, without a top-three cap.
    """
    stages: list[tuple[str, cp_model.LinearExprT]] = []
    people = {person.user_id: person for person in inp.people}
    for kind, label in KINDS:
        candidates = [pair for pair in found if pair.first.weekday() == kind]
        for day in sorted({pair.first for pair in candidates}):
            current = [pair for pair in candidates if pair.first == day]
            states = {}
            for pair in current:
                uid = pair.user_id
                history = people[uid].rest_turns.get(kind, RestTurnHistory())
                previous = [p for p in candidates if p.user_id == uid and p.first < day]
                count = max(0, history.count) + sum(p.var for p in previous)
                prior_date = history.last_date.toordinal() if history.last_date else 0
                last = model.new_int_var(
                    0, max(prior_date, day.toordinal()), f"turn_last_{kind}_{uid}_{day}"
                )
                # last_date is the pair's SECOND day, the date it is earned.
                model.add_max_equality(
                    last, [prior_date] + [(p.first.toordinal() + 1) * p.var for p in previous]
                )
                states[uid] = count, last
            ranks = []
            for receiver in current:
                uid = receiver.user_id
                count, last = states[uid]
                peers = [
                    p
                    for p in current
                    if p.user_id != uid and people[p.user_id].role == people[uid].role
                ]
                better = []
                for peer in peers:
                    peer_count, peer_last = states[peer.user_id]
                    stem = f"turn_{kind}_{uid}_{peer.user_id}_{day}"
                    more = model.new_bool_var(stem + "_more")
                    model.add(count > peer_count).only_enforce_if(more)
                    model.add(count <= peer_count).only_enforce_if(more.Not())
                    equal = model.new_bool_var(stem + "_equal")
                    model.add(count == peer_count).only_enforce_if(equal)
                    model.add(count != peer_count).only_enforce_if(equal.Not())
                    newer = model.new_bool_var(stem + "_newer")
                    model.add(last > peer_last).only_enforce_if(newer)
                    model.add(last <= peer_last).only_enforce_if(newer.Not())
                    tie = model.new_bool_var(stem + "_tie_priority")
                    model.add_min_equality(tie, [equal, newer])
                    priority = model.new_bool_var(stem + "_priority")
                    model.add_max_equality(priority, [more, tie])
                    better.append(priority)
                rank = model.new_int_var(0, len(peers), f"turn_rank_{kind}_{uid}_{day}")
                model.add(rank == len(peers) - sum(better))
                ranks.append((receiver, rank, len(peers)))
            base = len(current) + 1
            max_rank = max(top for _, _, top in ranks)
            name = f"rest_turns_{label}_{day.isoformat()}"
            if len(current) * base**max_rank < 2**60:
                rewards = []
                for pair, rank, top in ranks:
                    values = [base**level for level in range(top + 1)]
                    reward = model.new_int_var(
                        1, values[-1], f"turn_reward_{kind}_{pair.user_id}_{day}"
                    )
                    model.add_element(rank, values, reward)
                    earned = model.new_int_var(
                        0, values[-1], f"turn_earned_{kind}_{pair.user_id}_{day}"
                    )
                    model.add(earned == reward).only_enforce_if(pair.var)
                    model.add(earned == 0).only_enforce_if(pair.var.Not())
                    rewards.append(earned)
                stages.append((name, -sum(rewards)))
            else:
                # Equivalent lexicographic rank rewards without huge constants.
                for level in range(max_rank, -1, -1):
                    rewards = []
                    for pair, rank, top in ranks:
                        if level > top:
                            continue
                        at_rank = model.new_bool_var(
                            f"turn_rank{level}_{kind}_{pair.user_id}_{day}"
                        )
                        model.add(rank == level).only_enforce_if(at_rank)
                        model.add(rank != level).only_enforce_if(at_rank.Not())
                        earned = model.new_bool_var(
                            f"turn_earned{level}_{kind}_{pair.user_id}_{day}"
                        )
                        model.add_min_equality(earned, [pair.var, at_rank])
                        rewards.append(earned)
                    stages.append((f"{name}_rank_{level}", -sum(rewards)))
    return stages


def terms(model, found, inp, weight: int, spread_weight: int):
    """Compatibility wrapper; ordered engine callers use ``ordered_terms``.

    Scalar legacy point carry cannot be converted into independent turn
    histories. ``spread_weight`` remains accepted for source compatibility.
    """
    return [weight * expr for _, expr in ordered_terms(model, found, inp)]
