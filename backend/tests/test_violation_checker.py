"""F-09 recheck — the three rules added to mirror the engine (pure functions)."""

from __future__ import annotations

from app.models.enums import AttendanceCode, Role
from app.scheduler.calendar_utils import build_weeks, month_days
from app.services.schedule_violation_checker import (
    check_comp_days,
    check_min_a_days,
    check_off_chain,
    recheck,
)

A, D, X, CD, AL = (
    AttendanceCode.A, AttendanceCode.D, AttendanceCode.X, AttendanceCode.CD, AttendanceCode.AL,
)


def _full_month(uid: int, pattern: list[AttendanceCode], year=2032, month=3):
    days = month_days(year, month)
    grid = {(uid, d): pattern[i % len(pattern)] for i, d in enumerate(days)}
    return grid, build_weeks(days), days


def test_min_a_days_warns_only_for_role_a_in_full_month() -> None:
    grid, weeks, _ = _full_month(1, [D, D, D, D, D, X, X])
    assert check_min_a_days(grid, {1: Role.A}, weeks)  # 0 pure A → warning
    assert check_min_a_days(grid, {1: Role.T}, weeks) == []  # role T exempt
    grid_ok, weeks_ok, _ = _full_month(2, [A, D, A, D, D, X, X])
    assert check_min_a_days(grid_ok, {2: Role.A}, weeks_ok) == []
    # Partial month (diagnostic slice) is exempt like the engine.
    days = month_days(2032, 3)[:10]
    assert check_min_a_days({}, {1: Role.A}, build_weeks(days)) == []


def test_comp_days_shortfall_excess_and_non_a_roles() -> None:
    grid, weeks, days = _full_month(1, [A, D, A, D, D, X, X])
    # Owed 2, none scheduled → shortfall.
    assert any("owed" in w for w in check_comp_days(grid, {1: Role.A}, weeks, {1: 2}))
    # Owed 0, one CD scheduled → excess.
    grid[(1, days[0])] = CD
    assert any("only 0 owed" in w for w in check_comp_days(grid, {1: Role.A}, weeks, {}))
    # Exactly owed → clean.
    assert check_comp_days(grid, {1: Role.A}, weeks, {1: 1}) == []
    # Role T never earns comp days.
    assert any("never earns" in w for w in check_comp_days(grid, {1: Role.T}, weeks, {}))


def test_off_chain_flags_six_off_once_and_exempts_annual_leave() -> None:
    grid, weeks, days = _full_month(1, [A, D, A, D, D, X, X])
    for d in days[7:15]:  # days 8–15 off; with days 6–7 (X, X) the run starts day 6
        grid[(1, d)] = X
    warnings = check_off_chain(grid, {1: Role.A}, weeks, {})
    assert len(warnings) == 1 and str(days[5]) in warnings[0]
    # Same run as approved ANNUAL leave → sanctioned, no warning.
    for d in days[7:15]:
        grid[(1, d)] = AL
    assert check_off_chain(grid, {1: Role.A}, weeks, {1: set(days[7:15])}) == []


def test_recheck_includes_new_rules() -> None:
    grid, weeks, days = _full_month(1, [D, D, D, D, D, X, X])
    warnings = recheck(
        grid=grid, roles={1: Role.A}, carry_streaks={}, weeks=weeks,
        flight_pairs={d: 0 for d in days}, carry_comps={1: 1},
    )
    assert any("A-duty" in w for w in warnings)
    assert any("comp day" in w for w in warnings)
