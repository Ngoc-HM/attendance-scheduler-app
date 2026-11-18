"""Admin dashboard (customer 2026-11-18): one read of everything the admin
looks at first — who is on duty today, missing punches, requests waiting,
the state of this and next month's roster, and everyone's leave.

Nothing is stored: each part is read from the service that owns it, so the
dashboard always agrees with the page it summarises.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.business_time import business_today
from app.models.enums import Role, UserStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.schemas.dashboard import (
    DashboardDuty,
    DashboardLeave,
    DashboardMissing,
    DashboardRead,
    DashboardSchedule,
)
from app.services import (
    leave_balance,
    pending_counts_service,
    schedule_carry,
    schedule_service,
    time_clock_service,
)


def _schedule(db: Session, year: int, month: int) -> DashboardSchedule:
    schedule = (
        db.query(MonthlySchedule)
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
        .one_or_none()
    )
    # Only the carried days of the previous month's run: not created yet.
    if schedule is None or not schedule_carry.is_generated(db, schedule):
        return DashboardSchedule(year=year, month=month, status=None)
    return DashboardSchedule(
        year=year,
        month=month,
        status=schedule.status,
        violations=[v.message for v in schedule_service.violations_for(db, schedule.id)],
    )


def overview(db: Session) -> DashboardRead:
    today = business_today()
    # The admin account is left out, as on the attendance board.
    staff = (
        db.query(User)
        .filter(User.status == UserStatus.active, User.role != Role.M)
        .order_by(User.role, User.id)
        .all()
    )
    by_id = {u.id: u for u in staff}
    order = {u.id: n for n, u in enumerate(staff)}  # by group, then person

    def person(uid: int) -> dict:
        u = by_id[uid]
        return {"user_id": u.id, "code": u.code or u.username, "role": u.role}

    board = time_clock_service.board(db, today.year, today.month)
    punches = {c["user_id"]: c for c in board if c["work_date"] == today}
    cells = (
        db.query(ShiftAssignment)
        .join(MonthlySchedule, ShiftAssignment.schedule_id == MonthlySchedule.id)
        .filter(ShiftAssignment.work_date == today)
        .all()
    )
    working: list[DashboardDuty] = []
    off: list[DashboardDuty] = []
    for cell in sorted(
        (c for c in cells if c.user_id in by_id), key=lambda c: order[c.user_id]
    ):
        punch = punches.get(cell.user_id, {})
        duty = DashboardDuty(
            **person(cell.user_id),
            shift=cell.code,
            check_in_local=punch.get("check_in_local"),
            check_out_local=punch.get("check_out_local"),
        )
        (working if cell.code.is_working else off).append(duty)

    # Most recent day first: the admin deals with yesterday before last week.
    missing = [
        DashboardMissing(
            **person(c["user_id"]), work_date=c["work_date"], status=c["status"]
        )
        for c in sorted(
            (c for c in board if c["tint"] == "missing" and c["user_id"] in by_id),
            key=lambda c: (-c["work_date"].toordinal(), order[c["user_id"]]),
        )
    ]

    summaries = leave_balance.summaries(db, staff, today.year)
    following = leave_balance.summaries(db, staff, today.year + 1)
    ny, nm = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
    return DashboardRead(
        today=today,
        working=working,
        off=off,
        missing_clock=missing,
        pending=pending_counts_service.get_counts(db),
        this_month=_schedule(db, today.year, today.month),
        next_month=_schedule(db, ny, nm),
        leave_year=today.year,
        leave=[
            DashboardLeave(
                **person(u.id),
                quota=summaries[u.id].quota,
                used=summaries[u.id].used,
                pending=summaries[u.id].pending,
                available=summaries[u.id].available,
                next_used=following[u.id].used,
                next_pending=following[u.id].pending,
                next_available=following[u.id].available,
                carry_comp=u.carry_comp,
            )
            for u in staff
        ],
    )
