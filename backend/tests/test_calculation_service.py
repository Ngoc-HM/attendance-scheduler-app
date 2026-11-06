"""F-14 — carry-over math (pure) + month-close (integration)."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.enums import AttendanceCode, ScheduleStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.services import carry_over_math
from app.services.schedule_history import build_boundary_states

# --- pure carry_over_math --------------------------------------------------

def test_comp_balance_earned_minus_consumed() -> None:
    recs = [
        (date(2027, 9, 1), AttendanceCode.A_D),  # +1
        (date(2027, 9, 2), AttendanceCode.A_D),  # +1
        (date(2027, 9, 3), AttendanceCode.CD),   # -1
        (date(2027, 9, 4), AttendanceCode.A),    #  0
    ]
    assert carry_over_math.comp_balance(recs) == 1


def test_comp_balance_floors_at_zero() -> None:
    recs = [(date(2027, 9, 3), AttendanceCode.CD), (date(2027, 9, 4), AttendanceCode.CD)]
    assert carry_over_math.comp_balance(recs) == 0


def test_premium_off_counts_weekend_and_holiday_x() -> None:
    recs = [
        (date(2027, 9, 4), AttendanceCode.X),   # Sat → premium
        (date(2027, 9, 5), AttendanceCode.X),   # Sun → premium
        (date(2027, 9, 7), AttendanceCode.X),   # Tue, holiday → premium
        (date(2027, 9, 8), AttendanceCode.X),   # Wed, normal → NOT premium
        (date(2027, 9, 4), AttendanceCode.A),   # working Sat → not counted
    ]
    assert carry_over_math.premium_off_count(recs, holidays={date(2027, 9, 7)}) == 3


def test_trailing_streak_counts_run_to_month_end() -> None:
    recs = [
        (date(2027, 9, 28), AttendanceCode.X),
        (date(2027, 9, 29), AttendanceCode.A),
        (date(2027, 9, 30), AttendanceCode.D),
    ]
    assert carry_over_math.trailing_streak(recs) == 2
    off_last = recs[:-1] + [(date(2027, 9, 30), AttendanceCode.X)]
    assert carry_over_math.trailing_streak(off_last) == 0


# --- integration: close is idempotent --------------------------------------

def _admin(client: TestClient) -> dict[str, str]:
    res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_close_month_is_idempotent(client: TestClient) -> None:
    admin = _admin(client)
    res = client.post("/api/v1/users", headers=admin,
                      json={"username": "calc_u1", "password": "pass123",
                            "full_name": "Calc U1", "role": "A"})
    uid = res.json()["id"]

    # 2 A/D days this month → carry_comp should be 2.
    for day in ("2027-10-05", "2027-10-12"):
        client.put("/api/v1/attendance", headers=admin,
                   json={"user_id": uid, "work_date": day, "code": "A/D"})

    first = client.post("/api/v1/calculations/2027/10/close", headers=admin).json()
    assert first["users"][str(uid)]["carry_comp"] == 2

    # Re-running yields identical carry values (no double count).
    second = client.post("/api/v1/calculations/2027/10/close", headers=admin).json()
    assert second["users"][str(uid)]["carry_comp"] == 2

    summary = client.get("/api/v1/calculations/summary", headers=admin).json()
    assert summary[str(uid)]["carry_comp"] == 2


def test_close_month_equals_schedule_history(client: TestClient) -> None:
    """B6: month-close persists exactly what the scheduler derives from history."""
    admin = _admin(client)
    res = client.post("/api/v1/users", headers=admin,
                      json={"username": "calc_hist_a", "password": "pass123",
                            "full_name": "Calc Hist A", "role": "A"})
    uid = res.json()["id"]
    client.put("/api/v1/attendance", headers=admin,
               json={"user_id": uid, "work_date": "2026-11-03", "code": "A/D"})

    # Month end is still only planned (no actuals yet): X on Saturday 28th,
    # then A on 29-30. An actual-only close would ignore these cells.
    db = SessionLocal()
    try:
        schedule = (
            db.query(MonthlySchedule).filter_by(year=2026, month=11).one_or_none()
        )
        if schedule is None:
            schedule = MonthlySchedule(
                year=2026, month=11, status=ScheduleStatus.published
            )
            db.add(schedule)
            db.flush()
        for day, code in ((28, AttendanceCode.X), (29, AttendanceCode.A),
                          (30, AttendanceCode.A)):
            db.add(ShiftAssignment(schedule_id=schedule.id, user_id=uid,
                                   work_date=date(2026, 11, day), code=code))
        db.commit()
    finally:
        db.close()

    closed = client.post("/api/v1/calculations/2026/11/close", headers=admin)
    assert closed.status_code == 200

    db = SessionLocal()
    try:
        user = db.get(User, uid)
        state = build_boundary_states(db, [user], 2026, 12)[uid]
        assert user.carry_comp == state.carry_comp == 1
        assert user.carry_streak == state.carry_streak == 2
        assert user.carry_premium_off == state.carry_premium_off == 1
    finally:
        db.close()
