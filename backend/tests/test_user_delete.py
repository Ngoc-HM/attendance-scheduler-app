"""Deleting users with foreign keys enforced (review 2026-11-08 B2, B3; ruling R8).

R8: requests the deleted user decided keep their row with ``decided_by_id``
NULL (shift changes and self-arrange batches); a swap where the deleted user
is the counterpart is deleted while pending and kept with
``counterpart_user_id`` NULL once decided. An admin deleting their own account
is audited with ``actor_id=None`` and detail ``self``.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import func, text

from app.core.database import SessionLocal
from app.models.audit import AuditLog
from app.models.enums import LeaveStatus, Role, SwapKind
from app.models.self_arrange_request import SelfArrangeRequest
from app.models.shift_change_request import ShiftChangeRequest

V = "/api/v1"


def _bearer(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(
        f"{V}/auth/login", data={"username": username, "password": password}
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _admin(client: TestClient) -> dict[str, str]:
    return _bearer(client, "admin", "admin123")


def _create_user(client: TestClient, admin: dict[str, str], prefix: str, role: Role) -> int:
    username = f"{prefix}_{uuid.uuid4().hex[:8]}"
    res = client.post(
        f"{V}/users",
        headers=admin,
        json={
            "username": username,
            "password": "pass123",
            "full_name": username,
            "role": role.value,
        },
    )
    assert res.status_code == 201, res.text
    return int(res.json()["id"])


def _username(client: TestClient, admin: dict[str, str], user_id: int) -> str:
    users = client.get(f"{V}/users", headers=admin).json()
    return next(u["username"] for u in users if u["id"] == user_id)


def _add_shift_change(
    *,
    requester_id: int,
    status: LeaveStatus,
    decided_by_id: int | None = None,
    counterpart_user_id: int | None = None,
) -> int:
    db = SessionLocal()
    try:
        row = ShiftChangeRequest(
            requester_id=requester_id,
            work_date=date(2027, 5, 10),
            kind=SwapKind.swap_with,
            counterpart_user_id=counterpart_user_id,
            status=status,
            decided_by_id=decided_by_id,
            decided_at=datetime(2027, 5, 1, 9, 0) if decided_by_id else None,
        )
        db.add(row)
        db.commit()
        return int(row.id)
    finally:
        db.close()


def _shift_change(row_id: int) -> ShiftChangeRequest | None:
    db = SessionLocal()
    try:
        return db.get(ShiftChangeRequest, row_id)
    finally:
        db.close()


def test_sqlite_foreign_keys_enforced(client: TestClient) -> None:
    db = SessionLocal()
    try:
        if db.get_bind().dialect.name != "sqlite":
            return  # PostgreSQL always enforces foreign keys.
        assert db.execute(text("PRAGMA foreign_keys")).scalar() == 1
    finally:
        db.close()


def test_delete_admin_keeps_decided_shift_changes(client: TestClient) -> None:
    admin = _admin(client)
    admin2 = _create_user(client, admin, "del_admin_sc", Role.M)
    employee = _create_user(client, admin, "del_emp_sc", Role.T)
    row_id = _add_shift_change(
        requester_id=employee, status=LeaveStatus.approved, decided_by_id=admin2
    )

    res = client.delete(f"{V}/users/{admin2}", headers=admin)

    assert res.status_code == 204, res.text
    row = _shift_change(row_id)
    assert row is not None
    assert row.decided_by_id is None
    assert row.status is LeaveStatus.approved


def test_delete_admin_who_decided_self_arrange_returns_204(client: TestClient) -> None:
    admin = _admin(client)
    admin2 = _create_user(client, admin, "del_admin_sa", Role.M)
    employee = _create_user(client, admin, "del_emp_sa", Role.T)
    db = SessionLocal()
    try:
        row = SelfArrangeRequest(
            requester_id=employee,
            year=2027,
            month=5,
            changes=[{"work_date": "2027-05-10", "code": "AD"}],
            status=LeaveStatus.approved,
            decided_by_id=admin2,
            decided_at=datetime(2027, 5, 1, 9, 0),
        )
        db.add(row)
        db.commit()
        row_id = int(row.id)
    finally:
        db.close()

    res = client.delete(f"{V}/users/{admin2}", headers=admin)

    assert res.status_code == 204, res.text
    db = SessionLocal()
    try:
        kept = db.get(SelfArrangeRequest, row_id)
        assert kept is not None
        assert kept.decided_by_id is None
    finally:
        db.close()


def test_delete_counterpart_pending_request_removed_decided_kept(
    client: TestClient,
) -> None:
    admin = _admin(client)
    me = client.get(f"{V}/users/me", headers=admin).json()["id"]
    requester = _create_user(client, admin, "del_req", Role.T)
    counterpart = _create_user(client, admin, "del_cp", Role.T)
    pending_id = _add_shift_change(
        requester_id=requester,
        status=LeaveStatus.pending,
        counterpart_user_id=counterpart,
    )
    decided_id = _add_shift_change(
        requester_id=requester,
        status=LeaveStatus.rejected,
        counterpart_user_id=counterpart,
        decided_by_id=me,
    )

    res = client.delete(f"{V}/users/{counterpart}", headers=admin)

    assert res.status_code == 204, res.text
    assert _shift_change(pending_id) is None
    decided = _shift_change(decided_id)
    assert decided is not None
    assert decided.counterpart_user_id is None
    assert decided.decided_by_id == me


def test_admin_self_delete_returns_204_and_audits(client: TestClient) -> None:
    admin = _admin(client)
    admin2 = _create_user(client, admin, "del_self", Role.M)
    headers = _bearer(client, _username(client, admin, admin2), "pass123")
    db = SessionLocal()
    try:
        # SQLite reuses deleted user ids, so only count rows written from now on.
        last_audit_id = db.query(func.max(AuditLog.id)).scalar() or 0
    finally:
        db.close()

    res = client.delete(f"{V}/users/{admin2}", headers=headers)

    assert res.status_code == 204, res.text
    db = SessionLocal()
    try:
        rows = (
            db.query(AuditLog)
            .filter(
                AuditLog.id > last_audit_id,
                AuditLog.action == "user.delete",
                AuditLog.entity == "User",
                AuditLog.entity_id == admin2,
            )
            .all()
        )
        assert len(rows) == 1
        assert rows[0].actor_id is None
        assert rows[0].detail == "self"
    finally:
        db.close()


def test_refused_delete_writes_no_audit_row(client: TestClient) -> None:
    """A delete refused before any change (404) leaves no ``user.delete`` row."""
    admin = _admin(client)
    db = SessionLocal()
    try:
        before = db.query(AuditLog).filter(AuditLog.action == "user.delete").count()
    finally:
        db.close()

    assert client.delete(f"{V}/users/987654", headers=admin).status_code == 404

    db = SessionLocal()
    try:
        after = db.query(AuditLog).filter(AuditLog.action == "user.delete").count()
    finally:
        db.close()
    assert after == before
