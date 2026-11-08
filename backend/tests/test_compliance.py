"""§9.3 retention purge + §9.5 data-subject export."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core import business_time
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.attendance import AttendanceRecord
from app.models.audit import AuditLog
from app.models.enums import AttendanceCode
from app.models.user import User
from app.services import compliance_service

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


def test_export_contains_own_records_and_no_password(client: TestClient) -> None:
    admin = _admin(client)
    uid = _create(client, admin, "gdpr_a1", "A")
    client.put(f"{V}/attendance", headers=admin,
               json={"user_id": uid, "work_date": "2033-01-05", "code": "A"})

    me = _login(client, "gdpr_a1", "pass123")
    res = client.get(f"{V}/compliance/users/{uid}/export", headers=me)
    assert res.status_code == 200
    body = res.json()
    assert body["profile"]["username"] == "gdpr_a1"
    assert "hashed_password" not in body["profile"]
    assert any(r["work_date"] == "2033-01-05" for r in body["attendance_records"])

    # A colleague may not export someone else's data; an admin may.
    _create(client, admin, "gdpr_t1", "T")
    other = _login(client, "gdpr_t1", "pass123")
    assert client.get(f"{V}/compliance/users/{uid}/export", headers=other).status_code == 403
    assert client.get(f"{V}/compliance/users/{uid}/export", headers=admin).status_code == 200

    db = SessionLocal()
    try:
        assert db.query(AuditLog).filter(AuditLog.action == "compliance.user_export").count() >= 2
    finally:
        db.close()


def test_purge_respects_legal_floor_and_deletes_old_rows(client: TestClient) -> None:
    admin = _admin(client)
    uid = _create(client, admin, "gdpr_a2", "A")

    db = SessionLocal()
    try:
        db.add(AttendanceRecord(user_id=uid, work_date=date(2019, 3, 3), code=AttendanceCode.A))
        db.add(AttendanceRecord(user_id=uid, work_date=date(2033, 3, 3), code=AttendanceCode.A))
        db.commit()
    finally:
        db.close()

    # Cutoff more recent than 24 months ago → refused.
    res = client.post(f"{V}/compliance/retention/purge", headers=admin,
                      json={"before": date.today().isoformat()})
    assert res.status_code == 400

    # Non-admin → forbidden.
    assert client.post(f"{V}/compliance/retention/purge",
                       headers=_login(client, "gdpr_a2", "pass123"), json={}).status_code == 403

    res = client.post(f"{V}/compliance/retention/purge", headers=admin,
                      json={"before": "2020-01-01"})
    assert res.status_code == 200, res.text
    assert res.json()["cutoff"] == "2020-01-01"
    assert res.json()["deleted"]["attendance_records"] >= 1

    db = SessionLocal()
    try:
        remaining = {r.work_date for r in db.query(AttendanceRecord).filter_by(user_id=uid)}
        assert date(2019, 3, 3) not in remaining
        assert date(2033, 3, 3) in remaining
        assert db.query(AuditLog).filter(
            AuditLog.action == "compliance.retention_purge").count() >= 1
    finally:
        db.close()


def test_default_cutoff_uses_retention_months() -> None:
    assert compliance_service.default_cutoff(date(2030, 2, 15)) == date(2027, 2, 1)


def test_purge_floor_uses_effective_retention_floor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A DATA_RETENTION_MIN_MONTHS below the legal 24 months never lowers the
    purge floor: the service uses ``settings.retention_floor_months``."""
    monkeypatch.setattr(settings, "DATA_RETENTION_MIN_MONTHS", 12)
    with SessionLocal() as db, pytest.raises(HTTPException) as exc:
        # 18 months back: allowed by a 12-month floor, refused by the legal 24.
        compliance_service.purge_before(db, cutoff=date(1998, 7, 1), today=date(2000, 1, 1))
    assert exc.value.status_code == 400


def test_export_timestamp_uses_business_clock(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``exported_at`` comes from the (freezable) business clock in
    ``settings.TIMEZONE``, not the host's wall clock."""
    monkeypatch.setattr(settings, "TIMEZONE", "Europe/Berlin")
    monkeypatch.setattr(
        business_time, "_utcnow", lambda: datetime(2026, 12, 20, 23, 30, tzinfo=UTC)
    )
    with SessionLocal() as db:
        admin_id = db.query(User.id).filter(User.username == "admin").scalar()
        data = compliance_service.export_user_data(db, admin_id)
    assert data["exported_at"] == "2026-12-21T00:30:00+01:00"
