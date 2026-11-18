"""ORM → ``SolverInput`` mapping for schedule generation (F-07, §5.1).

Pure data assembly — no solving here, so it is testable against a DB fixture
without running OR-Tools. Pulls together every §5.1 input:

    people (active users + carry_* + previous-month codes + the good-pair
    points of the 12 months before), days,
    flight_pairs (F-04), approved leave (F-05/06), holidays
    (premium-off markers, decision #5).

The window runs past the month to the Sunday that ends its last week (owner
2026-11-18): the next month's carry days take their flights by weekday when
that month's plan is not entered yet (``flight_service.carry_flight_pairs``),
and their leave and holidays like any day. The month's own carried cells,
planned by the previous month's run, come in as facts (``carried.split``).
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import AttendanceCode, UserStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.scheduler import carried
from app.scheduler.calendar_utils import carry_days, month_days
from app.scheduler.domain import PersonInput, SolverInput
from app.services import flight_service, holiday_service, leave_service, schedule_history


def stored_carried_cells(
    db: Session, year: int, month: int
) -> dict[int, dict[date, AttendanceCode]]:
    """The month's carried cells: ``{user_id: {day: code}}``."""
    rows = (
        db.query(ShiftAssignment.user_id, ShiftAssignment.work_date, ShiftAssignment.code)
        .join(MonthlySchedule, ShiftAssignment.schedule_id == MonthlySchedule.id)
        .filter(
            MonthlySchedule.year == year,
            MonthlySchedule.month == month,
            ShiftAssignment.carried.is_(True),
        )
    )
    cells: dict[int, dict[date, AttendanceCode]] = {}
    for uid, day, code in rows:
        cells.setdefault(uid, {})[day] = code
    return cells


def build(db: Session, year: int, month: int, *, with_carry_days: bool = True) -> SolverInput:
    """Assemble the full ``SolverInput`` for one month.

    ``with_carry_days`` False: the window stops at the month's last day (the
    next month is generated already and keeps its cells).
    """
    users = db.query(User).filter(User.status == UserStatus.active).order_by(User.id).all()
    boundary = schedule_history.build_boundary_states(db, users, year, month)
    pair_points = schedule_history.carry_pair_points(db, {u.id for u in users}, year, month)
    turns = schedule_history.rest_turn_history(db, {u.id for u in users}, year, month)
    people = [
        PersonInput(
            user_id=u.id,
            role=u.role,
            carry_comp=boundary[u.id].carry_comp,
            carry_streak=boundary[u.id].carry_streak,
            carry_premium_off=boundary[u.id].carry_premium_off,
            prev_codes=boundary[u.id].prev_codes,
            carry_pair_points=pair_points[u.id],
            rest_turns=turns[u.id],
        )
        for u in users
    ]

    own = month_days(year, month)
    ahead = carry_days(year, month) if with_carry_days else []
    days = own + ahead
    # Five days cover every work-run window crossing the window's end.
    next_days = [days[-1] + timedelta(days=n) for n in range(1, 6)]
    # A week has at most six days in the previous month.
    prev_days = [days[0] - timedelta(days=n) for n in range(1, 7)]

    approved = leave_service.approved_off_map(db, year, month)
    annual = leave_service.annual_off_dates(db, year, month)
    holidays = holiday_service.holiday_dates(db, year, month)
    if ahead:
        ny, nm = ahead[0].year, ahead[0].month
        for uid, by_day in leave_service.approved_off_map(db, ny, nm).items():
            approved.setdefault(uid, {}).update({d: c for d, c in by_day.items() if d in ahead})
        for uid, leave_days in leave_service.annual_off_dates(db, ny, nm).items():
            annual.setdefault(uid, set()).update(d for d in leave_days if d in ahead)
        holidays |= {d for d in holiday_service.holiday_dates(db, ny, nm) if d in ahead}

    # The month's carried cells are facts: the stored code wins over the
    # leave map (a leave approved later was written into the cell already,
    # and an X it skipped stays ordinary rest).
    stored = stored_carried_cells(db, year, month)
    fixed, leave = carried.split(stored, {u.id: u.role for u in users})
    for uid, by_day in stored.items():
        for d in by_day:
            approved.get(uid, {}).pop(d, None)
    for uid, by_day in leave.items():
        approved.setdefault(uid, {}).update(by_day)

    return SolverInput(
        year=year,
        month=month,
        people=people,
        days=days,
        flight_pairs={
            **flight_service.flight_pairs_map(db, own),
            **flight_service.carry_flight_pairs(db, ahead),
        },
        approved_off={uid: by_day for uid, by_day in approved.items() if by_day},
        holidays=holidays,
        long_leave_off=annual,
        next_flight_pairs=flight_service.known_flight_pairs(db, next_days),
        prev_flight_pairs=flight_service.known_flight_pairs(db, prev_days),
        previous_working={u.id: boundary[u.id].previous_working for u in users},
        fixed=fixed,
        max_solve_seconds=settings.SOLVER_MAX_TIME_SECONDS,
    )
