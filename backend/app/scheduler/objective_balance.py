"""Monthly ordinary A/D fairness for role-A people only.

``ordered_terms`` minimizes every sorted individual absolute gap, worst first,
then aggregate balance and cross-person shift totals. The original ``terms``
and ``individual_terms`` builders remain available for source compatibility.
Emergency A/D never participates in an automatic solver run.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    """Cross-people A-versus-D spread penalties for role-A people."""
    role_a = [p for p in inp.people if p.role is Role.A]
    if len(role_a) < 2:
        return []  # a spread needs at least two people

    n_days = len(inp.days)
    penalties: list[cp_model.LinearExpr] = []

    for shift in (AttendanceCode.A, AttendanceCode.D):
        totals: list[cp_model.IntVar] = []
        for p in role_a:
            total = model.new_int_var(0, n_days, f"total_{shift.name}_{p.user_id}")
            model.add(total == sum(x[(p.user_id, d, shift)] for d in inp.days))
            totals.append(total)

        hi = model.new_int_var(0, n_days, f"max_{shift.name}")
        lo = model.new_int_var(0, n_days, f"min_{shift.name}")
        model.add_max_equality(hi, totals)
        model.add_min_equality(lo, totals)
        penalties.append(weight * (hi - lo))

    return penalties


def individual_terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    """Minimize |A-total - D-total| separately for every role-A person.

    Emergency A/D is intentionally outside the automatic solver domain.
    """
    n_days = len(inp.days)
    penalties: list[cp_model.LinearExpr] = []
    for person in inp.people:
        if person.role is not Role.A:
            continue
        total_a = sum(x[(person.user_id, day, AttendanceCode.A)] for day in inp.days)
        total_d = sum(x[(person.user_id, day, AttendanceCode.D)] for day in inp.days)
        gap = model.new_int_var(0, n_days, f"individual_ad_gap_{person.user_id}")
        model.add_abs_equality(gap, total_a - total_d)
        penalties.append(weight * gap)
    return penalties


def ordered_terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[tuple[str, cp_model.LinearExprT]]:
    """Minimize the sorted individual gaps, worst first, across every rank.

    A comparator network gives exact ordered gaps without exponential weights
    or a rank cutoff. Each expression is frozen before a lower stage runs.
    After individual fairness, prefer aggregate A/D equality and then equal
    shift totals across people. Only ordinary role-A shifts participate.
    """
    people = [p for p in inp.people if p.role is Role.A]
    if not people:
        return []
    bound = len(inp.days)
    gaps = []
    net_totals = []
    for person in people:
        net = sum(
            x[person.user_id, day, AttendanceCode.A] - x[person.user_id, day, AttendanceCode.D]
            for day in inp.days
        )
        gap = model.new_int_var(0, bound, f"ordered_ad_gap_{person.user_id}")
        model.add_abs_equality(gap, net)
        gaps.append(gap)
        net_totals.append(net)

    # Insertion sorting network (descending): all n ranks remain explicit.
    ranked: list[cp_model.IntVar] = []
    for i, gap in enumerate(gaps):
        carry = gap
        following = []
        for j, previous in enumerate(ranked):
            high = model.new_int_var(0, bound, f"ad_sort_hi_{i}_{j}")
            low = model.new_int_var(0, bound, f"ad_sort_lo_{i}_{j}")
            model.add_max_equality(high, [previous, carry])
            model.add_min_equality(low, [previous, carry])
            following.append(high)
            carry = low
        ranked = following + [carry]
    stages: list[tuple[str, cp_model.LinearExprT]] = [
        (f"ad_gap_rank_{i + 1}", gap) for i, gap in enumerate(ranked)
    ]
    aggregate = model.new_int_var(0, bound * len(people), "aggregate_ad_gap")
    model.add_abs_equality(aggregate, sum(net_totals))
    stages.append(("ad_aggregate_gap", aggregate))
    if len(people) > 1:
        stages.append(("ad_shift_spread", sum(terms(model, x, inp, 1))))
    return stages
