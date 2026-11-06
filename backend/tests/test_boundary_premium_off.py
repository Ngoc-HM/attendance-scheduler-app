"""F-14 — premium-off carry is derived from history, no month-close needed."""

from __future__ import annotations

from datetime import date

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, Role, UserStatus
from app.models.holiday import Holiday
from app.models.user import User
from app.services.schedule_history import build_boundary_states
from app.services.user_service import next_user_code


def test_premium_off_carry_counts_weekend_and_holiday_offs(client) -> None:
    db = SessionLocal()
    try:
        user = User(
            username="premium_hist_t",
            code=next_user_code(db, Role.T),
            full_name="Premium History T",
            hashed_password=get_password_hash("pass123"),
            role=Role.T,
            status=UserStatus.active,
            carry_premium_off=99,  # stale stored value must be ignored
        )
        db.add(user)
        db.add(Holiday(day=date(2034, 6, 7), name="Test holiday"))  # a Wednesday
        db.flush()
        for day, code in (
            (date(2034, 6, 3), AttendanceCode.X),   # Saturday → premium
            (date(2034, 6, 4), AttendanceCode.X),   # Sunday → premium
            (date(2034, 6, 7), AttendanceCode.X),   # holiday → premium
            (date(2034, 6, 8), AttendanceCode.X),   # Thursday → ordinary
            (date(2034, 6, 10), AttendanceCode.AD),  # working Saturday → no
        ):
            db.add(AttendanceRecord(user_id=user.id, work_date=day, code=code))
        db.commit()

        state = build_boundary_states(db, [user], 2034, 7)[user.id]
        assert state.carry_premium_off == 3
    finally:
        db.close()
