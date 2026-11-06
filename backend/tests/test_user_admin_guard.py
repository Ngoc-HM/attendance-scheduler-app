"""Guardrails around admin / fixed-team edits and the DELETE user flow (CSV TC-005/006/007/008)."""
from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.attendance import AttendanceRecord
from app.models.audit import AuditLog
from app.models.enums import AttendanceCode, LeaveStatus, LeaveType, Role, UserStatus
from app.models.leave import LeaveRequest
from app.models.user import User

V = "/api/v1"


@pytest.fixture(autouse=True)
def reset_db_state(request: pytest.FixtureRequest) -> None:
    """Wipe per-test data so each scenario starts from a known baseline.

    The shared test SQLite file is initialised once by ``conftest.py`` (via the
    ``client`` lifespan); we must run AFTER the lifespan has created the
    tables. Force ``client`` to be resolved first by depending on it, then
    clean the DB before the test body runs.
    """
    request.getfixturevalue("client")
    db = SessionLocal()
    try:
        seed = db.query(User).filter(User.username == "admin").one_or_none()
        if seed is not None:
            seed.role = Role.M
            seed.status = UserStatus.active
        non_seed = (
            db.query(User)
            .filter(User.username != "admin")
            .all()
        )
        for u in non_seed:
            db.query(AttendanceRecord).filter(
                AttendanceRecord.user_id == u.id
            ).delete(synchronize_session=False)
            db.query(LeaveRequest).filter(LeaveRequest.user_id == u.id).delete(
                synchronize_session=False
            )
            db.query(AuditLog).filter(AuditLog.actor_id == u.id).update(
                {AuditLog.actor_id: None}, synchronize_session=False
            )
            db.delete(u)
        db.commit()
    finally:
        db.close()
    yield

V = "/api/v1"


def _login(client: TestClient, username: str, password: str) -> str:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    return res.json()["access_token"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin(client: TestClient) -> dict[str, str]:
    return _bearer(_login(client, "admin", "admin123"))


def _create_user(client: TestClient, admin: dict, username: str, role: str) -> int:
    res = client.post(
        f"{V}/users",
        headers=admin,
        json={"username": username, "password": "pass123", "full_name": username, "role": role},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _fetch_user(user_id: int) -> User:
    db: Session = SessionLocal()
    try:
        return db.get(User, user_id)
    finally:
        db.close()


# --- TC-006 / TC-008: last-admin lockout ----------------------------------


def test_last_admin_cannot_self_demote(client: TestClient) -> None:
    """Seed admin (the only one) tries to change their own role to T → 409."""
    admin = _admin(client)
    me = client.get(f"{V}/users/me", headers=admin).json()
    res = client.patch(
        f"{V}/users/{me['id']}", headers=admin, json={"role": "T"}
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "You cannot remove or disable the last remaining admin."


def test_last_admin_cannot_be_disabled(client: TestClient) -> None:
    admin = _admin(client)
    me = client.get(f"{V}/users/me", headers=admin).json()
    res = client.patch(
        f"{V}/users/{me['id']}", headers=admin, json={"status": "disabled"}
    )
    assert res.status_code == 409


def test_admin_can_self_demote_when_another_admin_exists(client: TestClient) -> None:
    """Two admins → one may leave admin status because another remains."""
    admin = _admin(client)
    _create_user(client, admin, "admin2", Role.M.value)
    me = client.get(f"{V}/users/me", headers=admin).json()
    res = client.patch(
        f"{V}/users/{me['id']}", headers=admin, json={"role": "T"}
    )
    assert res.status_code == 200, res.text
    assert res.json()["user"]["role"] == "T"


def test_solo_admin_cannot_self_disable(client: TestClient) -> None:
    """When only one active admin remains, that admin cannot disable themselves."""
    admin = _admin(client)
    admin3_id = _create_user(client, admin, "admin3", Role.M.value)
    me = client.get(f"{V}/users/me", headers=admin).json()
    # Seed admin demotes themselves to T; admin3 is now the sole admin.
    res = client.patch(
        f"{V}/users/{me['id']}", headers=admin, json={"role": "T"}
    )
    assert res.status_code == 200

    # Re-login as admin3 to get a fresh token.
    admin3_token = client.post(
        f"{V}/auth/login", data={"username": "admin3", "password": "pass123"}
    ).json()["access_token"]
    headers = _bearer(admin3_token)

    # admin3 (the only active admin) tries to disable themselves → 409.
    res = client.patch(
        f"{V}/users/{admin3_id}", headers=headers, json={"status": "disabled"}
    )
    assert res.status_code == 409


# --- TC-005: fixed-team soft warning --------------------------------------


def test_emptying_fixed_team_returns_warning(client: TestClient) -> None:
    """When the last active A is demoted, PATCH succeeds but warnings[] is non-empty."""
    admin = _admin(client)
    fixed_id = _create_user(client, admin, "fixed_solo", Role.A.value)
    res = client.patch(
        f"{V}/users/{fixed_id}", headers=admin, json={"role": "T"}
    )
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "T"
    assert any("fixed" in w.lower() for w in res.json()["warnings"])


def test_fixed_team_warning_absent_when_other_active_fixed_remains(client: TestClient) -> None:
    admin = _admin(client)
    _create_user(client, admin, "fixed_keep", Role.A.value)
    target = _create_user(client, admin, "fixed_change", Role.A.value)
    res = client.patch(
        f"{V}/users/{target}", headers=admin, json={"role": "T"}
    )
    assert res.status_code == 200
    assert res.json()["warnings"] == []


def test_disabling_last_fixed_member_returns_warning(client: TestClient) -> None:
    """Disabling the only active `A` should warn (CSV TC-005 warn-only)."""
    admin = _admin(client)
    fixed_id = _create_user(client, admin, "fixed_last_active", Role.A.value)
    res = client.patch(
        f"{V}/users/{fixed_id}", headers=admin, json={"status": "disabled"}
    )
    assert res.status_code == 200
    assert res.json()["user"]["status"] == "disabled"
    assert any("fixed" in w.lower() for w in res.json()["warnings"])


def test_combined_role_and_status_change_does_not_duplicate_warning(
    client: TestClient,
) -> None:
    """A single PATCH that empties the fixed team should return exactly one warning."""
    admin = _admin(client)
    fixed_id = _create_user(client, admin, "fixed_combo", Role.A.value)
    res = client.patch(
        f"{V}/users/{fixed_id}",
        headers=admin,
        json={"role": "T", "status": "disabled"},
    )
    assert res.status_code == 200
    fixed_warnings = [
        w for w in res.json()["warnings"] if "fixed" in w.lower()
    ]
    assert len(fixed_warnings) == 1


# --- TC-007: delete user with cascade -------------------------------------


def test_delete_user_returns_204_and_removes_row(client: TestClient) -> None:
    admin = _admin(client)
    user_id = _create_user(client, admin, "deleteable", Role.T.value)
    res = client.delete(f"{V}/users/{user_id}", headers=admin)
    assert res.status_code == 204
    assert _fetch_user(user_id) is None


def test_delete_user_cascades_history(client: TestClient) -> None:
    """Attendance / leave / audit rows linked to the user disappear (actor→null)."""
    admin = _admin(client)
    user_id = _create_user(client, admin, "delete_with_history", Role.A.value)

    db: Session = SessionLocal()
    try:
        db.add(
            AttendanceRecord(
                user_id=user_id,
                work_date=date(2027, 3, 1),
                code=AttendanceCode.A,
                recorded_by=1,  # admin user
            )
        )
        db.add(
            LeaveRequest(
                user_id=user_id,
                start_date=date(2027, 3, 5),
                end_date=date(2027, 3, 6),
                leave_type=LeaveType.monthly,
                status=LeaveStatus.pending,
            )
        )
        db.add(
            AuditLog(
                actor_id=user_id,
                action="user.create",
                entity="User",
                entity_id=user_id,
            )
        )
        db.commit()
    finally:
        db.close()

    res = client.delete(f"{V}/users/{user_id}", headers=admin)
    assert res.status_code == 204

    db = SessionLocal()
    try:
        assert db.query(AttendanceRecord).filter_by(user_id=user_id).count() == 0
        assert db.query(LeaveRequest).filter_by(user_id=user_id).count() == 0
        # Other actors' audit logs that pointed at this user lose the FK but keep the row.
        assert db.query(AuditLog).filter_by(actor_id=user_id).count() == 0
        assert db.query(User).filter_by(id=user_id).one_or_none() is None
    finally:
        db.close()


def test_delete_last_admin_rejected(client: TestClient) -> None:
    admin = _admin(client)
    me = client.get(f"{V}/users/me", headers=admin).json()
    res = client.delete(f"{V}/users/{me['id']}", headers=admin)
    assert res.status_code == 409


def test_delete_nonexistent_user_returns_404(client: TestClient) -> None:
    admin = _admin(client)
    assert client.delete(f"{V}/users/9999", headers=admin).status_code == 404
