"""ORM → ``SolverInput`` mapping for schedule generation (F-07, §5.1).

Pure data assembly — no solving here, so it is testable against a DB fixture
without running OR-Tools. Pulls together every §5.1 input:

    people (active users + carry_*), days, 7-day blocks, flight_pairs (F-04),
    approved leave (F-05/06), holidays (premium-off markers, decision #5).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import UserStatus
from app.models.user import User
from app.scheduler.calendar_utils import build_weeks, month_days
from app.scheduler.domain import PersonInput, SolverInput
from app.services import flight_service, holiday_service, leave_service


def build(db: Session, year: int, month: int) -> SolverInput:
    """Assemble the full ``SolverInput`` for one month."""
    users = (
        db.query(User)
        .filter(User.status == UserStatus.active)
        .order_by(User.id)
        .all()
    )
    people = [
        PersonInput(
            user_id=u.id,
            role=u.role,
            carry_comp=u.carry_comp,
            carry_streak=u.carry_streak,
            carry_premium_off=u.carry_premium_off,
        )
        for u in users
    ]

    days = month_days(year, month)
    return SolverInput(
        year=year,
        month=month,
        people=people,
        days=days,
        weeks=build_weeks(days),
        flight_pairs=flight_service.flight_pairs_map(db, days),
        approved_off=leave_service.approved_off_map(db, year, month),
        holidays=holiday_service.holiday_dates(db, year, month),
        long_leave_off=leave_service.annual_off_dates(db, year, month),
        max_solve_seconds=settings.SOLVER_MAX_TIME_SECONDS,
    )
