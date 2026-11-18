"""Assemble the month's roster for the customer's workbook layout (#70).

Content is the planned roster of the month (``ShiftAssignment``, including
the admin's manual edits), not the recorded attendance, followed by the
carried days this month's generation planned into the next month (owner
2026-11-18). Comp figures and the
notes below the table come from the history the scheduler already reads
(actual attendance over the plan).
"""

from __future__ import annotations

import re
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.i18n import t
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, LeaveStatus, Role, UserStatus
from app.models.leave import LeaveRequest
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.scheduler.calendar_utils import month_days
from app.services import flight_service, holiday_service, schedule_carry, schedule_history
from app.services.flight_pair_derivation import ARRIVAL_TO_DEPARTURE
from app.services.roster_sheet import CompRow, RosterDay, RosterFlightRow, RosterPerson, RosterSheet

# Column order (owner 2026-11-18): by role, then by the number in the code.
ROLE_ORDER = [Role.M, Role.T, Role.F, Role.A]
# The workbook lists the SGN pair (31/30) before the HAN pair (37/36).
PAIR_ORDER = sorted(ARRIVAL_TO_DEPARTURE)
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def _code_number(code: str) -> int:
    match = re.search(r"\d+", code)
    return int(match.group()) if match else 0


def _people(db: Session, with_cells: set[int]) -> list[tuple[RosterPerson, User]]:
    """Active people, plus anyone else with a cell in the roster; never a
    pending sign-up."""
    users = db.query(User).filter(User.status != UserStatus.pending).all()
    users = [u for u in users if u.status is UserStatus.active or u.id in with_cells]
    users.sort(key=lambda u: (ROLE_ORDER.index(u.role), _code_number(u.code or ""),
                              u.code or "", u.id))
    return [(RosterPerson(u.id, u.code or "", u.role.value), u) for u in users]


def _hhmm(value) -> str:
    return value.strftime("%H%M") if value else ""


def _days(db: Session, days: list[date]) -> list[RosterDay]:
    legs = flight_service.list_flights_for_days(db, days)
    out = []
    for day in days:
        by_number = {f.flt_number: f for f in legs.get(day, [])}
        rows = []
        for arr in PAIR_ORDER:
            dep = ARRIVAL_TO_DEPARTURE[arr]
            if arr in by_number or dep in by_number:
                sta = by_number[arr].sta if arr in by_number else None
                std = by_number[dep].std if dep in by_number else None
                rows.append(RosterFlightRow(f"{arr}/{dep}", f"{_hhmm(sta)}/{_hhmm(std)}"))
        out.append(RosterDay(day, rows))
    return out


def _previous_month_cells(
    db: Session, year: int, month: int, ids: set[int]
) -> tuple[dict[tuple[int, date], AttendanceCode], dict[tuple[int, date], AttendanceCode]]:
    """(planned, actual) cells of the month before ``year/month``."""
    py, pm = schedule_history.previous_month(year, month)
    first, last = month_days(py, pm)[0], month_days(py, pm)[-1]
    planned = {
        (a.user_id, a.work_date): a.code
        for a in db.query(ShiftAssignment).filter(
            ShiftAssignment.user_id.in_(ids),
            ShiftAssignment.work_date >= first, ShiftAssignment.work_date <= last)
    }
    actual = {
        (r.user_id, r.work_date): r.code
        for r in db.query(AttendanceRecord).filter(
            AttendanceRecord.user_id.in_(ids),
            AttendanceRecord.work_date >= first, AttendanceRecord.work_date <= last)
    }
    return planned, actual


def _comp_notes(
    db: Session, year: int, month: int, people: list[RosterPerson]
) -> tuple[str, list[str]]:
    """One line per person with A/D days last month: ``A1: 2 - 03OCT A/D
    duty assigned // 21OCT A/D instead of D`` (instead of = the plan said
    otherwise and the recorded day is A/D)."""
    py, pm = schedule_history.previous_month(year, month)
    heading = f"Compensation Days from {MONTHS[pm - 1]} {py % 100:02d} as follows:"
    planned, actual = _previous_month_cells(db, year, month, {p.user_id for p in people})
    lines = []
    for person in people:
        items = []
        for day in month_days(py, pm):
            key = (person.user_id, day)
            code = actual.get(key, planned.get(key))
            if code is not AttendanceCode.A_D:
                continue
            plan = planned.get(key)
            tag = f"{day.day:02d}{MONTHS[pm - 1][:3].upper()}"
            if plan is not None and plan is not AttendanceCode.A_D:
                items.append(f"{tag} A/D instead of {plan.value}")
            else:
                items.append(f"{tag} A/D duty assigned")
        if items:
            lines.append(f"{person.code}: {len(items)} - " + " // ".join(items))
    return heading, lines


def _comp_rows(db, year, month, pairs, grid) -> dict[int, CompRow]:
    states = schedule_history.build_boundary_states(db, [u for _, u in pairs], year, month)
    holidays = holiday_service.holiday_dates(db, year, month)
    cut = settings.HOLIDAY_COMP_EFFECTIVE_FROM
    rows = {}
    for person, _ in pairs:
        cells = [(d, c) for (uid, d), c in grid.items() if uid == person.user_id]
        present = sum(
            int(c is AttendanceCode.A_D) + int(c.is_working and d in holidays and d >= cut)
            for d, c in cells
        )
        used = sum(1 for _, c in cells if c is AttendanceCode.CD)
        previous = states[person.user_id].carry_comp
        rows[person.user_id] = CompRow(present, previous, used,
                                       max(0, previous + present - used))
    return rows


def _leave(db: Session, year: int, ids: set[int]) -> dict[int, dict[int, int]]:
    """Approved leave days per person and month of ``year`` (calendar days,
    the count the leave balance uses)."""
    out: dict[int, dict[int, int]] = {uid: {} for uid in ids}
    requests = db.query(LeaveRequest).filter(
        LeaveRequest.user_id.in_(ids), LeaveRequest.status == LeaveStatus.approved,
        LeaveRequest.start_date <= date(year, 12, 31),
        LeaveRequest.end_date >= date(year, 1, 1))
    for req in requests:
        for m in range(1, 13):
            days = month_days(year, m)
            start, end = max(req.start_date, days[0]), min(req.end_date, days[-1])
            if start <= end:
                months = out[req.user_id]
                months[m] = months.get(m, 0) + (end - start).days + 1
    return out


def build(db: Session, year: int, month: int, admin: User) -> RosterSheet:
    schedule = (
        db.query(MonthlySchedule)
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
        .one_or_none()
    )
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("report.roster_no_schedule"))
    grid = {(a.user_id, a.work_date): a.code for a in schedule.assignments}
    # The carried days this month's run planned into the next month.
    following = schedule_carry.find(db, *schedule_carry.following_month(year, month))
    carried = schedule_carry.carried_cells(db, following.id) if following else []
    carry = sorted({a.work_date for a in carried})
    pairs = _people(db, {uid for uid, _ in grid} | {a.user_id for a in carried})
    people = [p for p, _ in pairs]
    heading, notes = _comp_notes(db, year, month, people)
    return RosterSheet(
        year=year, month=month, people=people,
        days=_days(db, month_days(year, month)),
        grid={**grid, **{(a.user_id, a.work_date): a.code for a in carried}},
        comp=_comp_rows(db, year, month, pairs, grid),
        carry_days=_days(db, carry),
        comp_heading=heading, comp_notes=notes, checked_by=admin.code or "",
        leave_days=_leave(db, year, {p.user_id for p in people}),
        leave_quota={u.id: u.annual_leave_quota for _, u in pairs},
    )
