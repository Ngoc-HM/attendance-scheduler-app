"""F-09 recheck — the three rules added to mirror the engine (pure functions)."""

from __future__ import annotations

from app.models.enums import AttendanceCode, Role
from app.scheduler.calendar_utils import month_days
from app.services.schedule_violation_checker import (
    check_comp_days,
    check_consecutive,
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
    return grid, days


def test_min_a_days_warns_only_for_role_a_in_full_month() -> None:
    grid, days = _full_month(1, [D, D, D, D, D, X, X])
    assert check_min_a_days(grid, {1: Role.A}, days)  # 0 pure A → warning
    assert check_min_a_days(grid, {1: Role.T}, days) == []  # role T exempt
    grid_ok, days_ok = _full_month(2, [A, D, A, D, D, X, X])
    assert check_min_a_days(grid_ok, {2: Role.A}, days_ok) == []
    # Partial month (diagnostic slice) is exempt like the engine.
    assert check_min_a_days({}, {1: Role.A}, month_days(2032, 3)[:10]) == []


def test_comp_days_shortfall_excess_and_non_a_roles() -> None:
    grid, days = _full_month(1, [A, D, A, D, D, X, X])
    # Owed 2, none scheduled → shortfall.
    [short] = check_comp_days(grid, {1: Role.A}, days, {1: 2})
    assert (short.rule, short.user_id, short.params) == (
        "comp_day_shortfall", 1, {"owed": 2, "amount": 2}
    )
    # Owed 0, one CD scheduled → excess.
    grid[(1, days[0])] = CD
    assert [w.rule for w in check_comp_days(grid, {1: Role.A}, days, {})] == [
        "comp_day_excess"
    ]
    # Exactly owed → clean.
    assert check_comp_days(grid, {1: Role.A}, days, {1: 1}) == []
    # Owner D1 (2026-11-06): every role earns CD by working a holiday, so the
    # same owed-versus-scheduled comparison applies to role T.
    assert any("only 0 owed" in w.message for w in check_comp_days(grid, {1: Role.T}, days, {}))
    assert check_comp_days(grid, {1: Role.T}, days, {1: 1}) == []


def test_off_chain_flags_six_off_once_and_exempts_annual_leave() -> None:
    grid, days = _full_month(1, [A, D, A, D, D, X, X])
    for d in days[7:15]:  # days 8–15 off; with days 6–7 (X, X) the run starts day 6
        grid[(1, d)] = X
    warnings = check_off_chain(grid, {1: Role.A}, days, {})
    assert len(warnings) == 1 and str(days[5]) in warnings[0].message
    assert (warnings[0].rule, warnings[0].day) == ("max_consecutive_off", days[5])
    # Same run as approved ANNUAL leave → sanctioned, no warning.
    for d in days[7:15]:
        grid[(1, d)] = AL
    assert check_off_chain(grid, {1: Role.A}, days, {1: set(days[7:15])}) == []


def test_recheck_includes_new_rules() -> None:
    grid, days = _full_month(1, [D, D, D, D, D, X, X])
    warnings = recheck(
        grid=grid, roles={1: Role.A}, carry_streaks={}, days=days,
        flight_pairs={d: 0 for d in days}, carry_comps={1: 1},
    )
    assert any("A-duty" in w.message for w in warnings)
    assert any("comp day" in w.message for w in warnings)


def test_checker_flags_carry_streak_six_then_work() -> None:
    """F7: a 6-day run carried in and continued on day 1 is reported.

    ``run == 6`` never fired when the carry was already 6 (the run jumped to
    7 on day 1); ``run >= 6`` reports once per run, at the breaching day.
    """
    days = month_days(2026, 9)
    AD = AttendanceCode.AD
    # Days 1–3 working, then short working runs (never more than 3 in a row).
    grid = {
        (1, d): AD if d.day <= 3 else (X if d.day % 5 in (0, 4) else AD)
        for d in days
    }
    breach = [f"User 1: more than 5 consecutive working days at {days[0]}"]
    for carry in (5, 6, 9):
        assert [
            w.message for w in check_consecutive(grid, {1: Role.T}, {1: carry}, days)
        ] == breach
    # Day 1 off breaks the carried run: nothing to report.
    grid[(1, days[0])] = X
    assert check_consecutive(grid, {1: Role.T}, {1: 6}, days) == []


def test_checker_flags_off_chain_after_annual_leave_start() -> None:
    """F7: six ordinary X days right after an annual leave are still a long
    ordinary break — the exemption covers the windows that contain leave, not
    the run behind it, exactly like the engine's window constraint."""
    days = month_days(2026, 9)
    annual = {d for d in days if d.day <= 3}
    grid = {
        (1, d): AL if d in annual else (X if d.day <= 9 else AttendanceCode.AD)
        for d in days
    }
    warnings = check_off_chain(grid, {1: Role.T}, days, {1: annual})
    assert len(warnings) == 1
    assert str(days[3]) in warnings[0].message
    # Five X after the leave (4–8) are allowed (ruling R1).
    grid[(1, days[8])] = AttendanceCode.AD
    assert check_off_chain(grid, {1: Role.T}, days, {1: annual}) == []


def test_off_chain_exempts_runs_with_monthly_leave() -> None:
    """Ruling R1 (C3): weekly X next to an approved MONTHLY leave (AL cells,
    not in ``annual_off``) form a legal off-run."""
    days = month_days(2027, 2)
    # X Mon 8, AL Tue 9 – Sat 13, X Sun 14: a 7-day run holding leave.
    grid = {
        (1, d): AL if 9 <= d.day <= 13 else (X if d.day in (8, 14) else AttendanceCode.AD)
        for d in days
    }
    assert check_off_chain(grid, {1: Role.T}, days, {}) == []
