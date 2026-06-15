"""§5.3 #4 + #6 — fixed-group staffing: bind, A/D substitution, slack."""

from __future__ import annotations

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days

DEMAND = {0: (0, 0), 1: (1, 1), 2: (1, 2)}


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


def _coverage(grid, fixed_ids, d):
    a = sum(1 for u in fixed_ids if grid[(u, d)] is AttendanceCode.A)
    dd = sum(1 for u in fixed_ids if grid[(u, d)] is AttendanceCode.D)
    ad = sum(1 for u in fixed_ids if grid[(u, d)] is AttendanceCode.A_D)
    return a + ad, dd + ad  # A/D covers one of each (§5.3 #6)


def test_daily_demand_met_exactly_per_flight_pairs() -> None:
    days = month_days(2026, 6)
    people = [
        PersonInput(1, Role.M),
        PersonInput(6, Role.A), PersonInput(7, Role.A),
        PersonInput(8, Role.A), PersonInput(9, Role.A),
    ]
    # Mix of 0/1/2-pair days.
    fp = {d: (d.day % 3) for d in days}
    out = _solve(people, days, fp)

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for d in days:
        assert _coverage(grid, (6, 7, 8, 9), d) == DEMAND[fp[d]]


def test_zero_pair_days_have_no_flight_codes() -> None:
    days = month_days(2026, 6)[:14]
    people = [PersonInput(6, Role.A), PersonInput(7, Role.A)]
    out = _solve(people, days, {d: 0 for d in days})

    assert out.feasible and not out.violations
    flight = {AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D}
    assert all(a.code not in flight for a in out.assignments)


def test_flexible_roles_never_cover_flight_demand() -> None:
    """§5.3 #4: demand is on the FIXED group; M/T default to O/D."""
    days = month_days(2026, 6)[:14]
    people = [
        PersonInput(1, Role.M), PersonInput(2, Role.T),
        PersonInput(6, Role.A), PersonInput(7, Role.A),
    ]
    out = _solve(people, days, {d: 1 for d in days})

    assert out.feasible and not out.violations
    flight = {AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D}
    mt = [a for a in out.assignments if a.user_id in (1, 2)]
    assert all(a.code not in flight for a in mt)
    assert {a.code for a in mt} <= {AttendanceCode.O_D, AttendanceCode.X}


def test_understaffed_day_reports_violation_with_ad_suggestion() -> None:
    """Slack path (§5.6): coverage gap → schedule still returned + Violation
    naming the day and suggesting the A/D fallback."""
    days = month_days(2026, 6)[:7]
    people = [PersonInput(6, Role.A)]  # one person, demand needs three
    out = _solve(people, days, {d: 2 for d in days})

    assert out.feasible
    assert len(out.assignments) == len(days)
    staffing = [v for v in out.violations if v.rule == "fixed_group_staffing"]
    assert staffing
    assert staffing[0].day is not None
    assert "A/D" in staffing[0].message  # §5.6 #13 suggestion
