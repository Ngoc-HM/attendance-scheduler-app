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
    attendance = client.put("/api/v1/attendance", headers=user,
                            json={"user_id": 1, "work_date": "2027-01-01", "code": "A"})
    assert attendance.status_code == 403
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


def test_user_lifecycle_and_manual_flight_entry_are_audited(client: TestClient) -> None:
    """Blocker #2 follow-up: user CRUD, approval, manual flight entry and
    month-close all leave an audit row."""
    admin = _admin(client)
    created = client.post("/api/v1/users", headers=admin,
                          json={"username": "audit_u1", "password": "pass123",
                                "full_name": "Audit U1", "role": "T"}).json()
    client.patch(f"/api/v1/users/{created['id']}", headers=admin, json={"full_name": "Renamed"})
    client.post("/api/v1/auth/register",
                json={"username": "audit_pending", "password": "pass123",
                      "full_name": "Pending"})
    pending_id = next(u["id"] for u in client.get("/api/v1/users", headers=admin).json()
                      if u["username"] == "audit_pending")
    client.post(f"/api/v1/auth/users/{pending_id}/approve", headers=admin,
                json={"role": "T"})
    client.put("/api/v1/flights/days", headers=admin, json={"day": "2029-02-02", "flight_pairs": 1})
    client.put("/api/v1/flights", headers=admin,
               json={"day": "2029-02-02", "flt_number": 37, "route": "HAN-FRA"})
    client.post("/api/v1/calculations/2029/1/close", headers=admin)
    client.delete(f"/api/v1/users/{created['id']}", headers=admin)

    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        actions = {r.action for r in db.query(AuditLog).all()}
    finally:
        db.close()
    for expected in (
        "user.create", "user.update", "user.approve", "user.delete",
        "flight.day.upsert", "flight.upsert", "calculations.close_month",
    ):
        assert expected in actions, expected


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
