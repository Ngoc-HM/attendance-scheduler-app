"""§5.3 #4 + #6 — flight-shift staffing FLOOR, A/D substitution, slack.

O/D is no longer auto-assigned: every working day is a real flight shift
(A / D / A/D) for every role, and the per-day flightPairs demand is a MINIMUM
floor (not an exact target) — matching the manual roster WR JUN26.
"""

from __future__ import annotations

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days

DEMAND = {0: (0, 0), 1: (1, 1), 2: (1, 2)}  # minimum (A, D) per flight pairs
FLIGHT = {AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D}


def _solve(people, days, flight_pairs):
    return SchedulerEngine().solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
            weeks=build_weeks(days),
            flight_pairs=flight_pairs,
            max_solve_seconds=15.0,
        )
    )


def _coverage(grid, ids, d):
    a = sum(1 for u in ids if grid[(u, d)] is AttendanceCode.A)
    dd = sum(1 for u in ids if grid[(u, d)] is AttendanceCode.D)
    ad = sum(1 for u in ids if grid[(u, d)] is AttendanceCode.A_D)
    return a + ad, dd + ad  # A/D covers one of each (§5.3 #6)


def test_daily_demand_floor_met_per_flight_pairs() -> None:
    """Coverage meets at least the per-pairs minimum, and O/D is never used."""
    days = month_days(2026, 6)
    ids = (1, 6, 7, 8, 9)
    people = [PersonInput(1, Role.M)] + [PersonInput(u, Role.A) for u in ids[1:]]
    fp = {d: (d.day % 3) for d in days}
    out = _solve(people, days, fp)

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for d in days:
        cov_a, cov_d = _coverage(grid, ids, d)
        min_a, min_d = DEMAND[fp[d]]
        assert cov_a >= min_a and cov_d >= min_d, (d, cov_a, cov_d)
    assert all(a.code is not AttendanceCode.O_D for a in out.assignments)


def test_od_never_auto_assigned_even_with_zero_pairs() -> None:
    """Working days are flight shifts; no O/D appears even with no flights."""
    days = month_days(2026, 6)[:14]
    people = [PersonInput(6, Role.A), PersonInput(7, Role.A)]
    out = _solve(people, days, {d: 0 for d in days})

    assert out.feasible and not out.violations
    allowed = FLIGHT | {AttendanceCode.X, AttendanceCode.CD}
    assert all(a.code in allowed for a in out.assignments)
    assert all(a.code is not AttendanceCode.O_D for a in out.assignments)


def test_flexible_roles_also_take_flight_shifts() -> None:
    """Every role now takes flight duty (no O/D) — M/T included (WR JUN26)."""
    days = month_days(2026, 6)[:14]
    people = [
        PersonInput(1, Role.M), PersonInput(2, Role.T),
        PersonInput(6, Role.A), PersonInput(7, Role.A),
    ]
    out = _solve(people, days, {d: 1 for d in days})

    assert out.feasible and not out.violations
    mt = [a for a in out.assignments if a.user_id in (1, 2)]
    assert all(a.code is not AttendanceCode.O_D for a in mt)
    assert any(a.code in FLIGHT for a in mt)  # M/T do get flight shifts


def test_understaffed_day_reports_violation_with_ad_suggestion() -> None:
    """Slack path (§5.6): coverage gap → schedule still returned + Violation
    naming the day and suggesting the A/D fallback."""
    days = month_days(2026, 6)[:7]
    people = [PersonInput(6, Role.A)]  # one person, demand needs 1 A + 2 D
    out = _solve(people, days, {d: 2 for d in days})

    assert out.feasible
    assert len(out.assignments) == len(days)
    staffing = [v for v in out.violations if v.rule == "flight_staffing"]
    assert staffing
    assert staffing[0].day is not None
    assert "A/D" in staffing[0].message  # §5.6 #13 suggestion
