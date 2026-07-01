"""Role-aware scheduling engine tests (owner decision 2026-06-26).

Verifies the per-role code domain, the cross-people A/D balance, the D>0
fix for role-A people, and the 2-X/week rule for every role.

Setup: 4 role-A + 3 role-T + 2 role-M people over a 14-day month slice,
with flight_pairs > 0 on several days.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days
from app.scheduler.role_codes import OFF_CODES, ROLE_CODES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ROLE_A_CODES = set(ROLE_CODES[Role.A])
ROLE_T_CODES = set(ROLE_CODES[Role.T])
ROLE_M_CODES = set(ROLE_CODES[Role.M])

# Use first 14 days of July 2026 (2 full 7-day blocks → clean 2 X per block).
_YEAR, _MONTH = 2026, 7
_DAYS = month_days(_YEAR, _MONTH)[:14]

# UIDs by role
_A_IDS = (10, 11, 12, 13)   # 4 role-A
_T_IDS = (20, 21, 22)        # 3 role-T
_M_IDS = (30, 31)            # 2 role-M

_PEOPLE = (
    [PersonInput(u, Role.A) for u in _A_IDS]
    + [PersonInput(u, Role.T) for u in _T_IDS]
    + [PersonInput(u, Role.M) for u in _M_IDS]
)

# Flights on days 3, 6, 9, 12 (1-indexed within the slice) — flight_pairs=2 on those.
_FLIGHT_PAIRS: dict[date, int] = {
    d: (2 if d.day in {3, 6, 9, 12} else 1)
    for d in _DAYS
}


@pytest.fixture(scope="module")
def solved():
    """Solve once; reuse across all tests in this module."""
    out = SchedulerEngine().solve(
        SolverInput(
            year=_YEAR,
            month=_MONTH,
            people=_PEOPLE,
            days=_DAYS,
            weeks=build_weeks(_DAYS),
            flight_pairs=_FLIGHT_PAIRS,
            max_solve_seconds=30.0,
        )
    )
    assert out.feasible, f"Solver returned infeasible: {out.violations}"
    return out


# ---------------------------------------------------------------------------
# Per-role domain assertions
# ---------------------------------------------------------------------------

def test_role_a_codes_only(solved) -> None:
    """Every role-A assignment uses a code in {A, D, A/D, X, CD}."""
    for a in solved.assignments:
        if a.user_id in _A_IDS:
            assert a.code in ROLE_A_CODES, (
                f"role-A user {a.user_id} on {a.day}: unexpected code {a.code}"
            )


def test_role_t_codes_only(solved) -> None:
    """Every role-T assignment uses a code in {AD, X}."""
    for a in solved.assignments:
        if a.user_id in _T_IDS:
            assert a.code in ROLE_T_CODES, (
                f"role-T user {a.user_id} on {a.day}: unexpected code {a.code}"
            )


def test_role_m_codes_only(solved) -> None:
    """Every role-M assignment uses a code in {O/D, X}."""
    for a in solved.assignments:
        if a.user_id in _M_IDS:
            assert a.code in ROLE_M_CODES, (
                f"role-M user {a.user_id} on {a.day}: unexpected code {a.code}"
            )


# (Per-person A≈D was intentionally dropped — incompatible with the HARD
#  §5.3 #4 staffing rule "2 pairs → 1 A + 2 D", which forces more D than A on
#  busy days. Balance is CROSS-PEOPLE only — see test_role_a_a_and_d_spread_is_small.)


def test_role_a_d_count_positive_when_flights_present(solved) -> None:
    """Original bug fix: total D across role-A must be > 0 when flights present.

    The bug was that only A was assigned (DEP count = 0). The hard staffing
    floor (1–2 D per flight day) now forces D to appear.
    """
    grid = {(a.user_id, a.day): a.code for a in solved.assignments}
    total_d = sum(
        1
        for uid in _A_IDS
        for d in _DAYS
        if grid[(uid, d)] in (AttendanceCode.D, AttendanceCode.A_D)
    )
    assert total_d > 0, "D count across role-A is 0 — the original D=0 bug is still present"


# ---------------------------------------------------------------------------
# 2 X per 7-day block for every role
# ---------------------------------------------------------------------------

def test_two_x_per_block_all_roles(solved) -> None:
    """Every person (all roles) gets exactly 2 X in each full 7-day block."""
    grid = {(a.user_id, a.day): a.code for a in solved.assignments}
    weeks = build_weeks(_DAYS)
    for p in _PEOPLE:
        for block in weeks:
            if len(block) < 7:
                continue  # skip partial blocks
            x_count = sum(1 for d in block if grid[(p.user_id, d)] is AttendanceCode.X)
            assert x_count == 2, (
                f"user {p.user_id} (role {p.role}): {x_count} X in block "
                f"starting {block[0]} (expected 2)"
            )


# ---------------------------------------------------------------------------
# Cross-people balance for role-A (spread)
# ---------------------------------------------------------------------------

def test_role_a_a_and_d_spread_is_small(solved) -> None:
    """F-08: max − min of A-totals and D-totals across role-A people <= 2."""
    grid = {(a.user_id, a.day): a.code for a in solved.assignments}
    for shift, extra in ((AttendanceCode.A, AttendanceCode.A_D),
                         (AttendanceCode.D, AttendanceCode.A_D)):
        totals = [
            sum(
                1 for d in _DAYS
                if grid[(uid, d)] in (shift, extra)
            )
            for uid in _A_IDS
        ]
        spread = max(totals) - min(totals)
        assert spread <= 2, (
            f"{shift.value} spread across role-A = {spread}: {totals}"
        )


# ---------------------------------------------------------------------------
# Role T/M never appear in flight staffing
# ---------------------------------------------------------------------------

def test_role_t_and_m_have_no_flight_codes(solved) -> None:
    """Role T and M never get A, D, or A/D — they are not flight-scheduled."""
    flight_codes = {AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D}
    for a in solved.assignments:
        if a.user_id in _T_IDS or a.user_id in _M_IDS:
            assert a.code not in flight_codes, (
                f"role-{'T' if a.user_id in _T_IDS else 'M'} user "
                f"{a.user_id} on {a.day}: unexpected flight code {a.code}"
            )
