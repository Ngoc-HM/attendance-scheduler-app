"""Independent chronological turn priorities, including peers beyond rank three."""

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import Role
from app.scheduler import objective_pair_points_fair
from app.scheduler.domain import PersonInput, RestTurnHistory, SolverInput
from app.scheduler.objective_off_pairing import BonusPair


def _solve(people, events, *, fixed=None, forbidden=None, optional=False):
    model = cp_model.CpModel()
    found = [
        BonusPair(uid, day, model.new_bool_var(f"p{uid}_{day}"), {4: 3, 5: 2, 6: 1}[day.weekday()])
        for day, eligible in events
        for uid in eligible
    ]
    for day, _ in events:
        choices = [p.var for p in found if p.first == day]
        model.add(sum(choices) <= 1) if optional else model.add(sum(choices) == 1)
    for uid, day in fixed or []:
        model.add(next(p.var for p in found if p.user_id == uid and p.first == day) == 1)
    for uid, day in forbidden or []:
        model.add(next(p.var for p in found if p.user_id == uid and p.first == day) == 0)
    inp = SolverInput(2027, 1, people, [], {})
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    for _, expr in objective_pair_points_fair.ordered_terms(model, found, inp):
        model.minimize(expr)
        assert solver.solve(model) == cp_model.OPTIMAL
        model.add(expr == solver.value(expr))
    return [(p.user_id, p.first) for p in found if solver.value(p.var)]


def _person(uid, *, count=0, last=None, kind=4, role=Role.T):
    return PersonInput(uid, role, rest_turns={kind: RestTurnHistory(count, last)})


def test_no_repeat_until_all_six_peers_have_a_turn():
    start = date(2027, 1, 1)
    events = [(start + timedelta(weeks=n), list(range(1, 7))) for n in range(6)]
    chosen = _solve([_person(uid) for uid in range(1, 7)], events)
    assert len({uid for uid, _ in chosen}) == 6


def test_count_precedes_waiting_time_and_equal_counts_use_oldest():
    people = [
        _person(1, count=2, last=date(2025, 1, 1)),
        _person(2, count=1, last=date(2026, 12, 20)),
        _person(3, count=1, last=date(2026, 10, 1)),
    ]
    assert _solve(people, [(date(2027, 1, 1), [1, 2, 3])]) == [(3, date(2027, 1, 1))]


def test_earlier_same_month_award_yields_next_turn_to_peer():
    fri = date(2027, 1, 1)
    next_fri = fri + timedelta(weeks=1)
    chosen = _solve([_person(1), _person(2)], [(fri, [1, 2]), (next_fri, [1, 2])], fixed=[(1, fri)])
    assert (2, next_fri) in chosen


def test_unavailable_member_retains_priority_when_they_return():
    fri = date(2027, 1, 1)
    chosen = _solve([_person(1), _person(2)], [(fri, [2]), (fri + timedelta(weeks=1), [1, 2])])
    assert (1, fri + timedelta(weeks=1)) in chosen


def test_pair_kinds_do_not_substitute_for_each_other():
    people = [
        PersonInput(1, Role.T, rest_turns={4: RestTurnHistory(10), 5: RestTurnHistory(0)}),
        PersonInput(2, Role.T, rest_turns={4: RestTurnHistory(0), 5: RestTurnHistory(10)}),
    ]
    fri = date(2027, 1, 1)
    chosen = _solve(people, [(fri, [1, 2]), (fri + timedelta(days=1), [1, 2])])
    assert chosen == [(2, fri), (1, fri + timedelta(days=1))]


def test_awards_are_not_suppressed_to_avoid_unfairness():
    people = [_person(1, count=20), _person(2)]
    fri = date(2027, 1, 1)
    assert _solve(people, [(fri, [1])], optional=True) == [(1, fri)]


def test_only_same_role_peers_compete():
    people = [_person(1, count=10), _person(2, count=0, role=Role.F)]
    fri = date(2027, 1, 1)
    assert len(_solve(people, [(fri, [1, 2])], optional=True)) == 1


def test_next_peer_precedes_more_awards_later_in_month():
    """Giving the oldest peer this Friday may preclude two later awards.

    A month-total reward used to choose all three turns for the recent leader.
    The owner's rotation order requires the available peer's turn now.
    """
    people = [
        _person(1, count=1, last=date(2026, 12, 25)),
        _person(2, count=1, last=date(2026, 10, 2)),
    ]
    model = cp_model.CpModel()
    fri = date(2027, 1, 1)
    found = [
        BonusPair(
            uid, fri + timedelta(weeks=week), model.new_bool_var(f"adversarial{uid}_{week}"), 3
        )
        for week, uids in [(0, [1, 2]), (1, [1]), (2, [1])]
        for uid in uids
    ]
    peer = next(p.var for p in found if p.user_id == 2)
    model.add(sum(p.var for p in found if p.first == fri) <= 1)
    for pair in found:
        if pair.first > fri:
            model.add(pair.var + peer <= 1)
    solver = cp_model.CpSolver()
    for _, expr in objective_pair_points_fair.ordered_terms(
        model, found, SolverInput(2027, 1, people, [], {})
    ):
        model.minimize(expr)
        assert solver.solve(model) == cp_model.OPTIMAL
        model.add(expr == solver.value(expr))
    assert solver.value(peer) == 1


def test_next_month_uses_previous_month_award_before_assigning_next_turn():
    january = date(2027, 1, 1)
    people = [_person(1), _person(2)]
    assert _solve(people, [(january, [1, 2])], fixed=[(1, january)]) == [(1, january)]
    # The service reconstructs this same state from genuine persisted X+X.
    february_people = [_person(1, count=1, last=january + timedelta(days=1)), _person(2)]
    february = date(2027, 2, 5)
    assert _solve(february_people, [(february, [1, 2])]) == [(2, february)]


def test_fifth_rank_yields_to_no_unavailable_lower_rank_and_precedes_sixth():
    friday = date(2027, 1, 1)
    people = [_person(uid, count=uid) for uid in range(1, 7)]
    assert _solve(
        people, [(friday, list(range(1, 7)))], forbidden=[(uid, friday) for uid in range(1, 5)]
    ) == [(5, friday)]


def test_available_leader_awarded_when_higher_priority_candidate_is_infeasible():
    friday = date(2027, 1, 1)
    people = [_person(1, count=20), _person(2)]
    assert _solve(people, [(friday, [1, 2])], forbidden=[(2, friday)], optional=True) == [
        (1, friday)
    ]


def test_large_role_group_uses_every_rank_without_integer_overflow():
    friday = date(2027, 1, 1)
    people = [_person(uid, count=uid) for uid in range(1, 18)]
    assert _solve(people, [(friday, list(range(1, 18)))]) == [(1, friday)]
