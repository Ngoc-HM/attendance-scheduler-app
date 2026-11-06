"""§9.1 — sickness (S) never reaches a colleague; no free text on sick days."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.enums import AttendanceCode
from app.models.schedule import ShiftAssignment

V = "/api/v1"


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _admin(client: TestClient) -> dict[str, str]:
    return _login(client, "admin", "admin123")


def _create(client: TestClient, admin: dict, username: str, role: str) -> int:
    res = client.post(
        f"{V}/users", headers=admin,
        json={"username": username, "password": "pass123", "full_name": username, "role": role},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_manual_override_rejects_sick_code(client: TestClient) -> None:
    admin = _admin(client)
    uid = _create(client, admin, "privacy_a1", "A")
    gen = client.post(f"{V}/schedules/generate", headers=admin, json={"year": 2032, "month": 3})
    sid = gen.json()["schedule"]["id"]
    res = client.post(
        f"{V}/schedules/{sid}/override", headers=admin,
        json={"user_id": uid, "work_date": "2032-03-03", "code": "S"},
    )
    assert res.status_code == 422
    assert "actual attendance" in res.json()["detail"]


def test_shift_change_request_rejects_sick_code(client: TestClient) -> None:
    admin = _admin(client)
    _create(client, admin, "privacy_t1", "T")
    user = _login(client, "privacy_t1", "pass123")
    res = client.post(
        f"{V}/shift-changes", headers=user,
        json={"work_date": "2032-03-10", "kind": "change_code", "requested_code": "S"},
    )
    assert res.status_code == 422


def test_legacy_sick_cell_masked_for_other_users_but_not_self(client: TestClient) -> None:
    """Defense in depth: an S already stored in a published grid is shown as X
    to colleagues and unchanged to the person themself; admins see it raw."""
    admin = _admin(client)
    sick_uid = _create(client, admin, "privacy_a2", "A")
    _create(client, admin, "privacy_t2", "T")
    gen = client.post(f"{V}/schedules/generate", headers=admin, json={"year": 2032, "month": 4})
    sid = gen.json()["schedule"]["id"]
    client.post(f"{V}/schedules/{sid}/publish", headers=admin)

    db = SessionLocal()
    try:
        cell = (
            db.query(ShiftAssignment)
            .filter(
                ShiftAssignment.schedule_id == sid,
                ShiftAssignment.user_id == sick_uid,
                ShiftAssignment.work_date == date(2032, 4, 6),
            )
            .one()
        )
        cell.code = AttendanceCode.S  # legacy / direct-DB write
        db.commit()
    finally:
        db.close()

    def cell_for(headers: dict) -> str:
        body = client.get(f"{V}/schedules/2032/4", headers=headers).json()
        return next(
            a["code"] for a in body["assignments"]
            if a["user_id"] == sick_uid and a["work_date"] == "2032-04-06"
        )

    assert cell_for(_login(client, "privacy_t2", "pass123")) == "X"
    assert cell_for(_login(client, "privacy_a2", "pass123")) == "S"
    assert cell_for(admin) == "S"


def test_sick_attendance_never_stores_a_note(client: TestClient) -> None:
    admin = _admin(client)
    uid = _create(client, admin, "privacy_a3", "A")
    sick = client.put(
        f"{V}/attendance", headers=admin,
        json={"user_id": uid, "work_date": "2032-05-04", "code": "S", "note": "flu, 39C"},
    )
    assert sick.status_code == 200
    assert sick.json()["note"] is None

    other = client.put(
        f"{V}/attendance", headers=admin,
        json={"user_id": uid, "work_date": "2032-05-05", "code": "T", "note": "safety course"},
    )
    assert other.json()["note"] == "safety course"

    me = client.get(
        f"{V}/attendance/me?year=2032&month=5", headers=_login(client, "privacy_a3", "pass123")
    ).json()
    sick_rows = [r for r in me if r["code"] == "S"]
    assert sick_rows and sick_rows[0]["note"] is None
