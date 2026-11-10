"""GET /pending-counts — admin navigation badges (owner 2026-11-10).

The test DB is shared across the session, so every count is asserted as a
delta against the value read at the start of the test.
"""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.enums import LeaveStatus, LeaveType, SwapKind
from app.models.leave import LeaveRequest
from app.models.shift_change_request import ShiftChangeRequest

V = "/api/v1"
URL = f"{V}/pending-counts"


def _bearer(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_user(client: TestClient, admin: dict[str, str], username: str) -> int:
    res = client.post(
        f"{V}/users", headers=admin,
        json={"username": username, "full_name": username, "password": "pass123",
              "role": "T"},
    )
    assert res.status_code == 201, res.text
    return int(res.json()["id"])


def _add_rows(user_id: int) -> tuple[int, int]:
    """One pending leave and shift change, plus decided
    rows of each kind that must not be counted."""
    db = SessionLocal()
    try:
        leave = LeaveRequest(
            user_id=user_id, start_date=date(2063, 3, 2), end_date=date(2063, 3, 3),
            leave_type=LeaveType.monthly, status=LeaveStatus.pending,
        )
        swap = ShiftChangeRequest(
            requester_id=user_id, work_date=date(2063, 3, 9),
            kind=SwapKind.change_code, status=LeaveStatus.pending,
        )
        decided = [
            LeaveRequest(
                user_id=user_id, start_date=date(2063, 4, 2), end_date=date(2063, 4, 9),
                leave_type=LeaveType.annual, status=LeaveStatus.approved,
            ),
            ShiftChangeRequest(
                requester_id=user_id, work_date=date(2063, 4, 9),
                kind=SwapKind.change_code, status=LeaveStatus.rejected,
            ),
        ]
        db.add_all([leave, swap, *decided])
        db.commit()
        return leave.id, swap.id
    finally:
        db.close()


def test_counts_follow_created_and_decided_items(client: TestClient) -> None:
    admin = _bearer(client, "admin", "admin123")
    before = client.get(URL, headers=admin)
    assert before.status_code == 200, before.text
    base = before.json()
    assert set(base) == {"leaves", "shift_changes", "users"}

    uid = _create_user(client, admin, "pc_requester")
    leave_id, swap_id = _add_rows(uid)
    reg = client.post(
        f"{V}/auth/register",
        json={"username": "pc_signup", "full_name": "pc_signup", "password": "pass123"},
    )
    assert reg.status_code == 201, reg.text

    after = client.get(URL, headers=admin).json()
    assert after == {k: base[k] + 1 for k in base}

    # Each decision drops its own number by one.
    rejected = {"status": "rejected"}
    for path in (f"/leaves/{leave_id}/decide", f"/shift-changes/{swap_id}/decide"):
        res = client.post(f"{V}{path}", headers=admin, json=rejected)
        assert res.status_code == 200, (path, res.text)
    res = client.post(
        f"{V}/auth/users/{reg.json()['id']}/approve", headers=admin, json={"role": "T"}
    )
    assert res.status_code == 200, res.text

    assert client.get(URL, headers=admin).json() == base


def test_employee_gets_403(client: TestClient) -> None:
    admin = _bearer(client, "admin", "admin123")
    _create_user(client, admin, "pc_employee")
    res = client.get(URL, headers=_bearer(client, "pc_employee", "pass123"))
    assert res.status_code == 403, res.text


def test_unauthenticated_gets_401(client: TestClient) -> None:
    assert client.get(URL).status_code == 401
