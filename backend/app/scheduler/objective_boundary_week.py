"""Boundary-week look-ahead for group A (owner data, 2026-11-12).

Rule W (``constraints_weekly_rest``) caps only this month's days of a last
week that ends next month. A real run showed the gap: December 2026 ends on
a Thursday, every group-A person worked all of Mon 28 – Thu 31 Dec, so in
January each of them owed 2 rest days among Fri 1 – Sun 3 — the four could
not cover the flights on 1 and 2 January (``flight_staffing``, slack proven).

So, when the month's last week runs r > 0 days into next month and there
are role-A people, every role-A person OWES next month

    owed = max(0, 2 − rest days in this month's part of that week)

(rest = any non-working code, pinned leave included), and those r days can
absorb

    capacity = Σ max(0, role-A people − people the flights need that day)

where the need is 3 for two flight pairs, 2 for one, 0 for none, read from
``SolverInput.next_flight_pairs`` and, for a day with no data yet, from the
same weekday of this month's last full Mon–Sun week. ``max(0, Σ owed −
capacity)`` is penalised per unit. An objective, never a reported rule: next
month's generation still judges the whole week with history.
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import OFF_CODES, codes_for

# People the flights need on a day, by flight pairs (1A+1D, 1A+2D; §5.3 #4).
NEED = {0: 0, 1: 2, 2: 3}
REST_PER_WEEK = 2


def _next_days(days: list[date]) -> list[date]:
    last = days[-1]
    return [last + timedelta(days=n) for n in range(1, 7 - last.weekday())]


def _pairs_ahead(inp: SolverInput, days: list[date], ahead: list[date]) -> dict[date, int]:
    """Flight pairs of the days ahead: known, else the same weekday of the
    month's last full Mon–Sun week (0 when there is none)."""
    in_month = set(days)
    full_mondays = [
        d for d in days
        if d.weekday() == 0 and d + timedelta(days=6) in in_month
    ]
    model_week = full_mondays[-1] if full_mondays else None
    out: dict[date, int] = {}
    for d in ahead:
        if d in inp.next_flight_pairs:
            out[d] = inp.next_flight_pairs[d]
        elif model_week is not None:
            out[d] = inp.flight_pairs.get(model_week + timedelta(days=d.weekday()), 0)
        else:
            out[d] = 0
    return out


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    days = sorted(inp.days)
    group_a = [p for p in inp.people if p.role is Role.A]
    if not days or not group_a:
        return []
    ahead = _next_days(days)
    if not ahead:
        return []  # the month ends on a Sunday
    tail = [d for d in days if d >= days[-1] - timedelta(days=days[-1].weekday())]
    pairs = _pairs_ahead(inp, days, ahead)
    capacity = sum(max(0, len(group_a) - NEED.get(pairs[d], 3)) for d in ahead)

    rest_codes = [c for c in codes_for(Role.A) if c in OFF_CODES]
    owed_vars: list[cp_model.IntVar] = []
    for p in group_a:
        rested = sum(x[(p.user_id, d, c)] for d in tail for c in rest_codes)
        owed = model.new_int_var(0, REST_PER_WEEK, f"boundary_owed_{p.user_id}")
        model.add(owed >= REST_PER_WEEK - rested)  # minimised: = max(0, 2 − rested)
        owed_vars.append(owed)
    excess = model.new_int_var(0, REST_PER_WEEK * len(group_a), "boundary_excess")
    model.add(excess >= sum(owed_vars) - capacity)
    return [weight * excess]
