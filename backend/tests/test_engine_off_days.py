"""§5.3 #2 — two X per 7-day block: bind test + slack/violation test."""

from __future__ import annotations

from datetime import date

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import (
    build_weeks,
    month_days,
    partial_block_off_target,
)


def _solve(people, days, flight_pairs=None, approved_off=None):
    return SchedulerEngine().solve(
        SolverInput(
            year=days[0].year,
            month=days[0].month,
            people=people,
            days=days,
            weeks=build_weeks(days),
            flight_pairs=flight_pairs or {d: 0 for d in days},
            approved_off=approved_off or {},
            max_solve_seconds=10.0,
        )
    )


def test_each_block_gets_exactly_target_x() -> None:
    """Feasible scenario → every block holds its pro-rated X target, 0 slack."""
    days = month_days(2026, 6)  # blocks 7/7/7/7/2 → targets 2/2/2/2/1
    people = [PersonInput(1, Role.T), PersonInput(2, Role.A)]
    out = _solve(people, days)

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for p in people:
        for block in build_weeks(days):
            got = sum(1 for d in block if grid[(p.user_id, d)] is AttendanceCode.X)
            assert got == partial_block_off_target(len(block))


def test_approved_leave_raises_block_target() -> None:
    """Decision #4: AL does not consume the 2-X quota — target goes up."""
    days = month_days(2026, 6)
    al_days = {date(2026, 6, 2): AttendanceCode.AL, date(2026, 6, 4): AttendanceCode.AL}
    people = [PersonInput(1, Role.T)]
    out = _solve(people, days, approved_off={1: al_days})

    assert out.feasible and not out.violations
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    first_block = build_weeks(days)[0]
    # 2 pinned AL (as X in decision layer) + 2 genuine X = 4 X cells total.
    got = sum(1 for d in first_block if grid[(1, d)] is AttendanceCode.X)
    assert got == 2 + 2


def test_impossible_quota_reports_violation_not_infeasible() -> None:
    """Slack path: a block fully pinned AL cannot fit 2 extra X → Violation."""
    days = month_days(2026, 6)[:7]  # a single 7-day block
    pinned = {d: AttendanceCode.AL for d in days}  # every day approved off
    people = [PersonInput(1, Role.T)]
    out = _solve(people, days, approved_off={1: pinned})

    assert out.feasible  # always-feasible architecture (decision #2)
    assert len(out.assignments) == len(days)
    offs = [v for v in out.violations if v.rule == "two_days_off_per_week"]
    assert offs and offs[0].user_id == 1
