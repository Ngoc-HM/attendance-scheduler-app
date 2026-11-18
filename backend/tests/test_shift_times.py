"""Shift time frames (decision #71): defaults, validation, derived A/D."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import pytest
from fastapi.testclient import TestClient

from app.core import business_time
from app.core.database import SessionLocal
from app.core.i18n import t
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode
from app.models.shift_time import ShiftTime
from app.models.user import User
from app.services.shift_time_service import DEFAULTS, double_frame, frame_for_code

V = "/api/v1"


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def clean_frames():
    """Each test starts from the owner's defaults (no stored rows)."""
    with SessionLocal() as db:
        db.query(ShiftTime).delete()
        db.commit()
    yield
    with SessionLocal() as db:
        db.query(ShiftTime).delete()
        db.commit()


def test_double_shift_frame_is_derived() -> None:
    assert double_frame(DEFAULTS) == (time(5, 30), time(13, 55))
    assert frame_for_code(DEFAULTS, AttendanceCode.AD) == (time(5, 30), time(13, 55))
    assert frame_for_code(DEFAULTS, AttendanceCode.D) == (time(6, 20), time(13, 55))
    assert frame_for_code(DEFAULTS, AttendanceCode.X) is None


def test_defaults_and_admin_update(client: TestClient, clean_frames) -> None:
    admin = _login(client, "admin", "admin123")
    res = client.get(f"{V}/shift-times", headers=admin)
    assert res.json() == [
        {"code": "A", "start": "05:30", "end": "13:05", "derived": False},
        {"code": "D", "start": "06:20", "end": "13:55", "derived": False},
        {"code": "A/D", "start": "05:30", "end": "13:55", "derived": True},
    ]
    res = client.put(f"{V}/shift-times", headers=admin, json={"frames": [
        {"code": "A", "start": "05:00", "end": "13:00"},
        {"code": "D", "start": "06:30", "end": "14:10"}]})
    assert res.status_code == 200, res.text
    assert res.json()[2] == {"code": "A/D", "start": "05:00", "end": "14:10", "derived": True}


def test_validation(client: TestClient, clean_frames) -> None:
    admin = {**_login(client, "admin", "admin123"), "Accept-Language": "vi"}
    bad = client.put(f"{V}/shift-times", headers=admin,
                     json={"frames": [{"code": "A", "start": "5:30", "end": "13:05"}]})
    assert bad.status_code == 400
    assert bad.json()["detail"] == t("shift_time.invalid_time", "vi")
    late = client.put(f"{V}/shift-times", headers=admin,
                      json={"frames": [{"code": "D", "start": "14:00", "end": "13:55"}]})
    assert late.status_code == 400
    assert late.json()["detail"] == t("shift_time.start_not_before_end", "vi")
    other = client.put(f"{V}/shift-times", headers=admin,
                       json={"frames": [{"code": "A/D", "start": "05:00", "end": "14:00"}]})
    assert other.status_code == 422  # only A and D are stored


def test_employee_reads_but_cannot_write(client: TestClient, monkeypatch, clean_frames) -> None:
    admin = _login(client, "admin", "admin123")
    res = client.post(f"{V}/users", headers=admin, json={
        "username": "shift_emp", "password": "pass123", "full_name": "Shift Emp", "role": "A"})
    assert res.status_code in (201, 409), res.text
    emp = _login(client, "shift_emp", "pass123")
    assert client.get(f"{V}/shift-times", headers=emp).status_code == 200
    put = client.put(f"{V}/shift-times", headers=emp,
                     json={"frames": [{"code": "A", "start": "05:00", "end": "13:00"}]})
    assert put.status_code == 403

    day = date(2076, 6, 9)
    monkeypatch.setattr(business_time, "_utcnow",
                        lambda: datetime(2076, 6, 9, 8, 0, tzinfo=UTC))
    assert client.get(f"{V}/shift-times/today", headers=emp).json() == {
        "code": None, "start": None, "end": None}
    with SessionLocal() as db:
        uid = db.query(User.id).filter(User.username == "shift_emp").scalar()
        db.add(AttendanceRecord(user_id=uid, work_date=day, code=AttendanceCode.A_D))
        db.commit()
    assert client.get(f"{V}/shift-times/today", headers=emp).json() == {
        "code": "A/D", "start": "05:30", "end": "13:55"}
