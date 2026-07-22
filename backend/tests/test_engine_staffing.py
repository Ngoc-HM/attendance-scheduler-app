"""§5.3 #4 — flight staffing floor without automatic A/D assignment.

Role-aware (owner decision 2026-06-26): flight-pair coverage is counted across
role-A people only.  Role T gets AD (full-day, no shift split); role M gets
O/D (office duty).  The per-day flightPairs demand is a MINIMUM floor (not an
exact target).
"""

from __future__ import annotations

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days

DEMAND = {0: (0, 0), 1: (1, 1), 2: (1, 2)}  # minimum (A, D) per flight pairs
FLIGHT_A = {AttendanceCode.A, AttendanceCode.D}


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


def _coverage(grid, role_a_ids, d):
    """Count A and D coverage across role-A people only."""
    a = sum(1 for u in role_a_ids if grid[(u, d)] is AttendanceCode.A)
    dd = sum(1 for u in role_a_ids if grid[(u, d)] is AttendanceCode.D)
    return a, dd


def test_daily_demand_floor_met_per_flight_pairs() -> None:
    """Coverage meets at least the per-pairs minimum across role-A people."""
    days = month_days(2026, 6)
    role_a_ids = (6, 7, 8, 9)
    # Role M gets O/D — does NOT count toward flight coverage.
    people = [PersonInput(1, Role.M)] + [PersonInput(u, Role.A) for u in role_a_ids]
    fp = {d: (d.day % 3) for d in days}
    out = _solve(people, days, fp)

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for d in days:
        cov_a, cov_d = _coverage(grid, role_a_ids, d)
        min_a, min_d = DEMAND[fp[d]]
        assert cov_a >= min_a and cov_d >= min_d, (d, cov_a, cov_d)
    # Role M always gets O/D; role A never gets O/D.
    m_codes = {a.code for a in out.assignments if a.user_id == 1}
    assert m_codes <= {AttendanceCode.O_D, AttendanceCode.X}
    a_codes = {a.code for a in out.assignments if a.user_id in role_a_ids}
    assert AttendanceCode.O_D not in a_codes


def test_od_never_auto_assigned_to_role_a() -> None:
    """Role-A working days are flight shifts; O/D never appears for role A."""
    days = month_days(2026, 6)[:14]
    people = [PersonInput(6, Role.A), PersonInput(7, Role.A)]
    out = _solve(people, days, {d: 0 for d in days})

    assert out.feasible and not out.violations
    allowed = FLIGHT_A | {AttendanceCode.X, AttendanceCode.CD}
    assert all(a.code in allowed for a in out.assignments)
    assert all(a.code is not AttendanceCode.O_D for a in out.assignments)


def test_role_t_gets_ad_and_role_m_gets_od() -> None:
    """Role-aware model: M → O/D on working days; T → AD on working days."""
    days = month_days(2026, 6)[:14]
    people = [
        PersonInput(1, Role.M), PersonInput(2, Role.T),
        PersonInput(6, Role.A), PersonInput(7, Role.A), PersonInput(8, Role.A),
    ]
    out = _solve(people, days, {d: 1 for d in days})

    assert out.feasible and not out.violations
    # Role M: only O/D or X
    m_codes = {a.code for a in out.assignments if a.user_id == 1}
    assert m_codes <= {AttendanceCode.O_D, AttendanceCode.X}
    # Role T: only AD or X
    t_codes = {a.code for a in out.assignments if a.user_id == 2}
    assert t_codes <= {AttendanceCode.AD, AttendanceCode.X}
    # Role A automatic schedule: only A, D, X, CD.
    a_codes = {a.code for a in out.assignments if a.user_id in (6, 7, 8)}
    assert a_codes <= FLIGHT_A | {AttendanceCode.X, AttendanceCode.CD}


def test_understaffed_day_reports_violation_without_auto_ad() -> None:
    """Slack path (§5.6): coverage gap → schedule still returned + Violation
    while the automatic schedule still contains no A/D."""
    days = month_days(2026, 6)[:7]
    people = [PersonInput(6, Role.A)]  # one person, demand needs 1 A + 2 D
    out = _solve(people, days, {d: 2 for d in days})

    assert out.feasible
    assert len(out.assignments) == len(days)
    staffing = [v for v in out.violations if v.rule == "flight_staffing"]
    assert staffing
    assert staffing[0].day is not None
    assert "will not assign an A/D" in staffing[0].message
    assert all(item.code is not AttendanceCode.A_D for item in out.assignments)
