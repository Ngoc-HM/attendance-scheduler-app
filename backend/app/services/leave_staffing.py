"""Flight-staffing risk of a leave request (role-A requesters only).

One rule set serves both the warning returned when the admin approves a
leave (``leave_service.decide``) and the risk lines kept on that request's
row in the admin's leave list, so the row shows exactly what approving said.
Nothing is stored: the lines are computed on demand, in the request's
language.

Per day of the span that has flight demand (``DEMAND``: 1 pair → 1 ARR +
1 DEP, 2 pairs → 1 ARR + 2 DEP):

- the day's month HAS a schedule → read the roster. The leave matters that
  day only when the requester's own cell is AL (approved request) or a
  working code (pending request); a day already off for them (X/CD, ...)
  changes nothing and is skipped. The other active role-A people on ARR
  (A, A/D) and DEP (D, A/D) are counted and each short shift is reported
  (``leave.staffing_short_shift``);
- the month has NO schedule yet → head count: active role-A people minus
  those on another approved leave that day minus the requester (pending or
  approved alike), against the ARR + DEP demand
  (``leave.staffing_headcount``).

``load`` reads everything a list needs in a fixed number of queries (role-A
users, flight days, schedules and their role-A cells, approved leaves); the
per-request work is then in memory.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.enums import AttendanceCode, LeaveStatus, Role, UserStatus
from app.models.flight import FlightDay
from app.models.leave import LeaveRequest
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.schemas.leave import LeaveRead
from app.services.schedule_violation_checker import DEMAND
from app.services.schedule_violation_text import format_day

_ARR_CODES = {AttendanceCode.A, AttendanceCode.A_D}
_DEP_CODES = {AttendanceCode.D, AttendanceCode.A_D}
_RISK_STATUSES = {LeaveStatus.pending, LeaveStatus.approved}


@dataclass
class StaffingContext:
    """What the risk check reads, loaded once for a set of requests."""

    role_a_ids: set[int] = field(default_factory=set)
    flight_pairs: dict[date, int] = field(default_factory=dict)
    scheduled_months: set[tuple[int, int]] = field(default_factory=set)
    cells: dict[tuple[int, date], AttendanceCode] = field(default_factory=dict)
    approved: list[LeaveRequest] = field(default_factory=list)


def _span(req: LeaveRequest) -> list[date]:
    return [
        req.start_date + timedelta(days=i)
        for i in range((req.end_date - req.start_date).days + 1)
    ]


def load(db: Session, reqs: Iterable[LeaveRequest]) -> StaffingContext:
    """Everything needed to judge ``reqs`` — five queries whatever their number."""
    role_a_ids = {
        uid
        for (uid,) in db.query(User.id).filter(
            User.role == Role.A, User.status == UserStatus.active
        )
    }
    relevant = [
        r for r in reqs if r.status in _RISK_STATUSES and r.user_id in role_a_ids
    ]
    ctx = StaffingContext(role_a_ids=role_a_ids)
    if not relevant:
        return ctx
    first = min(r.start_date for r in relevant)
    last = max(r.end_date for r in relevant)

    ctx.flight_pairs = {
        row.day: row.flight_pairs
        for row in db.query(FlightDay).filter(
            FlightDay.day >= first, FlightDay.day <= last
        )
    }

    months: set[tuple[int, int]] = set()
    month = date(first.year, first.month, 1)
    while month <= last:
        months.add((month.year, month.month))
        month = (month + timedelta(days=32)).replace(day=1)
    schedules = (
        db.query(MonthlySchedule.id, MonthlySchedule.year, MonthlySchedule.month)
        .filter(MonthlySchedule.year.between(first.year, last.year))
        .all()
    )
    schedule_ids = [sid for sid, y, m in schedules if (y, m) in months]
    ctx.scheduled_months = {(y, m) for _, y, m in schedules if (y, m) in months}
    if schedule_ids:
        ctx.cells = {
            (uid, day): code
            for uid, day, code in db.query(
                ShiftAssignment.user_id,
                ShiftAssignment.work_date,
                ShiftAssignment.code,
            ).filter(
                ShiftAssignment.schedule_id.in_(schedule_ids),
                ShiftAssignment.user_id.in_(role_a_ids),
                ShiftAssignment.work_date >= first,
                ShiftAssignment.work_date <= last,
            )
        }

    ctx.approved = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.status == LeaveStatus.approved,
            LeaveRequest.user_id.in_(role_a_ids),
            LeaveRequest.start_date <= last,
            LeaveRequest.end_date >= first,
        )
        .all()
    )
    return ctx


def warnings_for(ctx: StaffingContext, req: LeaveRequest) -> list[str]:
    """The request's staffing-risk lines, one per short day (or shift)."""
    if req.status not in _RISK_STATUSES or req.user_id not in ctx.role_a_ids:
        return []  # T/M/F (and disabled people) never count toward coverage
    others = ctx.role_a_ids - {req.user_id}
    lines: list[str] = []
    for day in _span(req):
        need_a, need_d = DEMAND.get(ctx.flight_pairs.get(day, 0), (0, 0))
        if need_a + need_d == 0:
            continue
        if (day.year, day.month) in ctx.scheduled_months:
            lines += _roster_lines(ctx, req, others, day, need_a, need_d)
        else:
            lines += _headcount_lines(ctx, req, others, day, need_a, need_d)
    return lines


def _roster_lines(
    ctx: StaffingContext,
    req: LeaveRequest,
    others: set[int],
    day: date,
    need_a: int,
    need_d: int,
) -> list[str]:
    own = ctx.cells.get((req.user_id, day))
    matters = (
        own is AttendanceCode.AL
        if req.status is LeaveStatus.approved
        else own is not None and own.is_working
    )
    if not matters:
        return []  # already off that day (X/CD, re-coded, no cell)
    arr = sum(1 for u in others if ctx.cells.get((u, day)) in _ARR_CODES)
    dep = sum(1 for u in others if ctx.cells.get((u, day)) in _DEP_CODES)
    return [
        t("leave.staffing_short_shift").format(
            day=format_day(day),
            amount=need - have,
            shift=t(f"schedule.violation.shift_{shift}"),
        )
        for shift, have, need in (("A", arr, need_a), ("D", dep, need_d))
        if have < need
    ]


def _headcount_lines(
    ctx: StaffingContext,
    req: LeaveRequest,
    others: set[int],
    day: date,
    need_a: int,
    need_d: int,
) -> list[str]:
    away = {
        o.user_id
        for o in ctx.approved
        if o.id != req.id and o.start_date <= day <= o.end_date
    }
    remaining = len(others - away)
    if remaining >= need_a + need_d:
        return []
    return [
        t("leave.staffing_headcount").format(
            day=format_day(day), remaining=remaining, need_a=need_a, need_d=need_d
        )
    ]


def staffing_warnings(db: Session, req: LeaveRequest) -> list[str]:
    """Risk lines for one request (the decision-time warning)."""
    return warnings_for(load(db, [req]), req)


def with_staffing_warnings(
    db: Session, reqs: Sequence[LeaveRequest]
) -> list[LeaveRead]:
    """The admin's leave list, each request carrying its current risk lines."""
    ctx = load(db, reqs)
    return [
        LeaveRead.model_validate(r).model_copy(
            update={"staffing_warnings": warnings_for(ctx, r)}
        )
        for r in reqs
    ]
