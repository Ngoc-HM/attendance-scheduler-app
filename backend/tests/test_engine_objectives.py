"""§5.4 soft objectives — balance, weekend pairing, premium-off fairness."""

from __future__ import annotations

from datetime import date

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days

SAT, SUN = 5, 6


def _solve(people, days, flight_pairs=None, holidays=None):
    return SchedulerEngine().solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
            weeks=build_weeks(days),
            flight_pairs=flight_pairs or {d: 0 for d in days},
            holidays=holidays or set(),
            max_solve_seconds=15.0,
        )
    )


def test_balance_spread_is_minimal_across_fixed_group() -> None:
    """§5.4 #7 (weight 100): A and D counts near-equal across fixed group."""
    days = month_days(2026, 6)
    fixed_ids = (6, 7, 8, 9)
    people = [PersonInput(u, Role.A) for u in fixed_ids]
    out = _solve(people, days, flight_pairs={d: 2 for d in days})

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for shift in (AttendanceCode.A, AttendanceCode.D):
        totals = [
            sum(1 for d in days
                if grid[(u, d)] in (shift, AttendanceCode.A_D))
            for u in fixed_ids
        ]
        assert max(totals) - min(totals) <= 1, f"{shift}: {totals}"


def test_weekly_offs_not_forced_onto_weekend() -> None:
    """Owner decision 2026-06-18: Sat/Sun are ordinary working days — the two
    weekly OFF days must NOT all be dumped on the weekend. We keep the 2-per-7
    quota but no longer reward Sat+Sun pairing, so the offs no longer pile up
    on every weekend (fairness/rotation is left to the premium-off objective)."""
    days = month_days(2026, 6)
    people = [PersonInput(1, Role.T)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}

    # Quota still holds: exactly 2 OFF days in each full 7-day block.
    for block in build_weeks(days):
        if len(block) >= 7:
            offs = sum(1 for d in block if grid[(1, d)] is AttendanceCode.X)
            assert offs == 2, f"block {block[0]}: {offs} offs"

    # And they are NOT all forced onto Sat+Sun every week any more.
    satsun_pairs = sum(
        1
        for d in days
        if d.weekday() == SAT
        and d.replace(day=d.day + 1) in set(days)
        and grid[(1, d)] is AttendanceCode.X
        and grid[(1, d.replace(day=d.day + 1))] is AttendanceCode.X
    )
    assert satsun_pairs < 4  # June 2026 has 4 Sat+Sun pairs; not all dumped there


def test_premium_off_balances_against_carry() -> None:
    """Decision #6: the person who already enjoyed premium offs yields
    weekend/holiday offs to the other."""
    days = month_days(2026, 2)  # Feb 2026: exactly 4 full blocks
    fresh = PersonInput(1, Role.T, carry_premium_off=0)
    served = PersonInput(2, Role.T, carry_premium_off=6)
    out = _solve([fresh, served], days)

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    prem = [d for d in days if d.weekday() in (SAT, SUN)]

    def premium_x(uid: int) -> int:
        return sum(1 for d in prem if grid[(uid, d)] is AttendanceCode.X)

    assert premium_x(1) > premium_x(2)


def test_holiday_counts_as_premium_day() -> None:
    """Decision #5/#6: holidays are working days, but an X there is premium."""
    days = month_days(2026, 6)
    holiday = date(2026, 6, 17)  # a Wednesday
    fresh = PersonInput(1, Role.T, carry_premium_off=0)
    served = PersonInput(2, Role.T, carry_premium_off=20)
    out = _solve([fresh, served], days, holidays={holiday})

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    # The holiday is NOT auto-off: at least one of them works it — and working
    # now means a real flight shift (O/D is no longer auto-assigned).
    codes = {grid[(1, holiday)], grid[(2, holiday)]}
    assert codes & {AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D}
