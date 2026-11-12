"""ORM → ``SolverInput`` mapping for schedule generation (F-07, §5.1).

Pure data assembly — no solving here, so it is testable against a DB fixture
without running OR-Tools. Pulls together every §5.1 input:

    people (active users + carry_* + previous-month codes + the good-pair
    points of the 12 months before), days,
    flight_pairs (F-04), approved leave (F-05/06), holidays
    (premium-off markers, decision #5).
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import UserStatus
from app.models.user import User
from app.scheduler.calendar_utils import month_days
from app.scheduler.domain import PersonInput, SolverInput
from app.services import flight_service, holiday_service, leave_service, schedule_history


def build(db: Session, year: int, month: int) -> SolverInput:
    """Assemble the full ``SolverInput`` for one month."""
    users = (
        db.query(User)
        .filter(User.status == UserStatus.active)
        .order_by(User.id)
        .all()
    )
    boundary = schedule_history.build_boundary_states(db, users, year, month)
    pair_points = schedule_history.carry_pair_points(db, {u.id for u in users}, year, month)
    people = [
        PersonInput(
            user_id=u.id,
            role=u.role,
            carry_comp=boundary[u.id].carry_comp,
            carry_streak=boundary[u.id].carry_streak,
            carry_premium_off=boundary[u.id].carry_premium_off,
            prev_codes=boundary[u.id].prev_codes,
            carry_pair_points=pair_points[u.id],
        )
        for u in users
    ]

    days = month_days(year, month)
    # Next month's days up to the Sunday closing this month's last week.
    next_days = [days[-1] + timedelta(days=n) for n in range(1, 7 - days[-1].weekday())]
    return SolverInput(
        year=year,
        month=month,
        people=people,
        days=days,
        flight_pairs=flight_service.flight_pairs_map(db, days),
        approved_off=leave_service.approved_off_map(db, year, month),
        holidays=holiday_service.holiday_dates(db, year, month),
        long_leave_off=leave_service.annual_off_dates(db, year, month),
        next_flight_pairs=flight_service.known_flight_pairs(db, next_days),
        previous_working={
            u.id: boundary[u.id].previous_working for u in users
        },
        max_solve_seconds=settings.SOLVER_MAX_TIME_SECONDS,
    )
