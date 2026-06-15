"""§9 — RBAC enforcement + audit-trail writing across admin mutations."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.audit import AuditLog


def _admin(client: TestClient) -> dict[str, str]:
    res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _make_nonadmin(client, admin, username) -> dict[str, str]:
    client.post("/api/v1/users", headers=admin,
                json={"username": username, "password": "pass123",
                      "full_name": username, "role": "T"})
    tok = client.post("/api/v1/auth/login",
                      data={"username": username, "password": "pass123"}).json()
    return {"Authorization": f"Bearer {tok['access_token']}"}


def test_non_admin_blocked_from_admin_mutations(client: TestClient) -> None:
    admin = _admin(client)
    user = _make_nonadmin(client, admin, "rbac_t1")

    # Each admin-only mutation → 403 for a normal user.
    assert client.put("/api/v1/holidays", headers=user,
                      json={"day": "2027-01-01", "name": "x"}).status_code == 403
    assert client.put("/api/v1/attendance", headers=user,
                      json={"user_id": 1, "work_date": "2027-01-01", "code": "A"}).status_code == 403
    assert client.post("/api/v1/schedules/generate", headers=user,
                       json={"year": 2027, "month": 1}).status_code == 403
    assert client.get("/api/v1/reports/monthly/2027/1", headers=user).status_code == 403


def test_non_admin_cannot_read_others_sick_via_admin_list(client: TestClient) -> None:
    """§9.1 — the month-wide attendance list (which may carry S) is admin-only;
    a user only reaches their own data via /attendance/me."""
    admin = _admin(client)
    user = _make_nonadmin(client, admin, "rbac_t2")
    assert client.get("/api/v1/attendance?year=2027&month=1", headers=user).status_code == 403
    assert client.get("/api/v1/attendance/me?year=2027&month=1", headers=user).status_code == 200


def test_admin_mutation_writes_audit_row(client: TestClient) -> None:
    admin = _admin(client)
    res = client.put("/api/v1/holidays", headers=admin,
                     json={"day": "2028-01-01", "name": "New Year"})
    assert res.status_code == 200

    # The audit trail recorded the action (§9.5).
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        rows = db.query(AuditLog).filter(AuditLog.action == "holiday.upsert").all()
        assert any(r.entity == "Holiday" for r in rows)
        assert all(r.actor_id is not None for r in rows)
    finally:
        db.close()
