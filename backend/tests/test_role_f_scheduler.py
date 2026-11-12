"""Role F is T-like (owner decision 2026-07-22).

F shares T's working domain {AD, X}, so it MUST obey the same
consecutive-working rule as T. This module
regresses the 2026-07-22 bug where F was exempted from the consecutive rule,
letting the solver produce 6+ working days in a row before 2 off days.

Assertions:
  * F assignments use only {AD, X}.
  * No 6-consecutive-day all-working window (the max-5 rule, same as T).
"""

from __future__ import annotations

from datetime import date

import pytest

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import month_days
from app.scheduler.role_codes import ROLE_CODES
from tests.rest_invariants import assert_rest_rules

_YEAR, _MONTH = 2026, 7
_DAYS = month_days(_YEAR, _MONTH)[:14]  # a two-week slice
_F_IDS = (40, 41, 42)                   # 3 role-F people

_PEOPLE = [PersonInput(u, Role.F) for u in _F_IDS]

# F is never flight-scheduled, so minimal flight_pairs (shape only).
_FLIGHT_PAIRS: dict[date, int] = {d: 1 for d in _DAYS}


@pytest.fixture(scope="module")
def solved():
    out = SchedulerEngine().solve(
        SolverInput(
            year=_YEAR,
            month=_MONTH,
            people=_PEOPLE,
            days=_DAYS,
            flight_pairs=_FLIGHT_PAIRS,
            max_solve_seconds=30.0,
        )
    )
    assert out.feasible, f"Solver returned infeasible: {out.violations}"
    return out


def test_role_f_codes_only(solved) -> None:
    """Every F assignment uses a code in {AD, X}."""
    f_codes = set(ROLE_CODES[Role.F])
    for a in solved.assignments:
        if a.user_id in _F_IDS:
            assert a.code in f_codes, (
                f"role-F user {a.user_id} on {a.day}: unexpected code {a.code}"
            )


def test_role_f_rest_rule(solved) -> None:
    """No F person works more than 5 days in a row (owner 2026-11-12)."""
    grid = {(a.user_id, a.day): a.code for a in solved.assignments}
    for p in _PEOPLE:
        assert_rest_rules(grid, p.user_id, _DAYS)


def test_role_f_no_six_consecutive_working(solved) -> None:
    """No 6-day window is fully working — the max-5-consecutive rule (§5.3 #3).

    This is the 2026-07-22 regression: previously F was exempted here, so the
    solver placed offs only to satisfy the old 2-X/block quota and left 6+ day
    work streaks.
    """
    grid = {(a.user_id, a.day): a.code for a in solved.assignments}
    for p in _PEOPLE:
        for i in range(len(_DAYS) - 5):
            window = _DAYS[i : i + 6]
            working = sum(
                1
                for d in window
                if grid[(p.user_id, d)] is not AttendanceCode.X
            )
            assert working <= 5, (
                f"user {p.user_id}: {working} working days in the 6-day window "
                f"starting {window[0]} (max 5 consecutive)"
            )