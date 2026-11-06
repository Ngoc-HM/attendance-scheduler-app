"""Unit + integration tests for shift-change request service (decision #8, spec §3).

Coverage targets:
- create own-cell ok.
- missing requested_code for change_code kind → 400.
- missing counterpart_user_id for swap_with kind → 400.
- strict_review true for A role, false for T role.
- decide approve → status approved + "schedule application pending" warning.
- re-decide → 409.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.models.enums import LeaveStatus, SwapKind

V = "/api/v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client, username, password):
    return client.post(f"{V}/auth/login", data={"username": username, "password": password})


def _token(client, username, password):
    return _login(client, username, password).json()["access_token"]


def _bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


def _create_user(client, admin_headers, username, role="A"):
    r = client.post(
        f"{V}/users",
        headers=admin_headers,
        json={
            "username": username, "full_name": username.title(),
            "password": "secret1", "role": role,
        },
    )
    assert r.status_code == 201
    return r.json()


def _get_db():
    from app.core.database import get_db
    gen = get_db()
    return next(gen)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestShiftChangeService:
    def _admin_headers(self, client):
        return _bearer(_token(client, "admin", "admin123"))

    def test_create_own_cell_ok(self, client: TestClient):
        """User can create a change_code request with valid fields."""
        admin = self._admin_headers(client)
        user = _create_user(client, admin, "sc_create_ok", role="A")
        uid = user["id"]

        db = _get_db()
        try:
            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 10),
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.X,
            )
            req, strict_review = shift_change_service.create_request(db, uid, payload)
            assert req.id is not None
            assert req.requester_id == uid
            assert req.status == LeaveStatus.pending
            assert strict_review is True  # A is fixed
        finally:
            db.close()

    def test_missing_code_returns_400(self, client: TestClient):
        """change_code kind without requested_code → 400 swap.code_required."""
        admin = self._admin_headers(client)
        user = _create_user(client, admin, "sc_no_code", role="T")
        uid = user["id"]

        db = _get_db()
        try:
            from fastapi import HTTPException

            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 10),
                kind=SwapKind.change_code,
                requested_code=None,  # missing
            )
            with pytest.raises(HTTPException) as exc_info:
                shift_change_service.create_request(db, uid, payload)
            assert exc_info.value.status_code == 400
        finally:
            db.close()

    def test_missing_counterpart_returns_400(self, client: TestClient):
        """swap_with kind without counterpart_user_id → 400 swap.counterpart_required."""
        admin = self._admin_headers(client)
        user = _create_user(client, admin, "sc_no_counterpart", role="T")
        uid = user["id"]

        db = _get_db()
        try:
            from fastapi import HTTPException

            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 10),
                kind=SwapKind.swap_with,
                counterpart_user_id=None,  # missing
            )
            with pytest.raises(HTTPException) as exc_info:
                shift_change_service.create_request(db, uid, payload)
            assert exc_info.value.status_code == 400
        finally:
            db.close()

    def test_strict_review_true_for_a(self, client: TestClient):
        """A role → strict_review is True."""
        admin = self._admin_headers(client)
        user = _create_user(client, admin, "sc_a_strict", role="A")
        uid = user["id"]

        db = _get_db()
        try:
            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 15),
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.D,
            )
            _, strict_review = shift_change_service.create_request(db, uid, payload)
            assert strict_review is True
        finally:
            db.close()

    def test_strict_review_false_for_t(self, client: TestClient):
        """T role → strict_review is False."""
        admin = self._admin_headers(client)
        user = _create_user(client, admin, "sc_t_flexible", role="T")
        uid = user["id"]

        db = _get_db()
        try:
            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 15),
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.X,
            )
            _, strict_review = shift_change_service.create_request(db, uid, payload)
            assert strict_review is False
        finally:
            db.close()

    def test_decide_approve_without_schedule_raises_409(self, client: TestClient):
        """Phase 05: approving a change with NO schedule for that month is an
        error (409 swap.no_schedule) — there is nothing to apply it to."""
        admin = self._admin_headers(client)
        user = _create_user(client, admin, "sc_approve_warn", role="A")
        uid = user["id"]

        db = _get_db()
        try:
            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 20),
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.A,
            )
            req, _ = shift_change_service.create_request(db, uid, payload)
            from app.models.user import User

            admin_user = db.query(User).filter_by(username="admin").first()

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                shift_change_service.decide(
                    db, req.id, LeaveStatus.approved, admin_id=admin_user.id
                )
            assert exc_info.value.status_code == 409
            db.rollback()
            db.refresh(req)
            assert req.status == LeaveStatus.pending  # not silently approved
        finally:
            db.close()

    def test_re_decide_returns_409(self, client: TestClient):
        """Re-deciding an already-decided request → 409 swap.already_decided."""
        admin = self._admin_headers(client)
        user = _create_user(client, admin, "sc_redecide", role="A")
        uid = user["id"]

        db = _get_db()
        try:
            from fastapi import HTTPException

            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 22),
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.D,
            )
            req, _ = shift_change_service.create_request(db, uid, payload)
            from app.models.user import User

            admin_user = db.query(User).filter_by(username="admin").first()

            # First decision succeeds (reject needs no schedule to apply to).
            shift_change_service.decide(db, req.id, LeaveStatus.rejected, admin_id=admin_user.id)

            # Second decision on same request → 409.
            with pytest.raises(HTTPException) as exc_info:
                shift_change_service.decide(
                    db, req.id, LeaveStatus.approved, admin_id=admin_user.id
                )
            assert exc_info.value.status_code == 409
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Requestable codes: employees ask only for their regular working / off codes
# (the role's solver domain minus CD). Leave and comp days have their own flows.
# ---------------------------------------------------------------------------

_NOT_REQUESTABLE = "Employees may only request their regular working or off codes."


def _request(client, username, body):
    headers = _bearer(_token(client, username, "secret1"))
    return client.post(f"{V}/shift-changes", headers=headers, json=body)


@pytest.mark.parametrize("code", ["AL", "CD"])
def test_requesting_leave_or_comp_code_is_refused(client: TestClient, code: str):
    admin = _bearer(_token(client, "admin", "admin123"))
    _create_user(client, admin, f"f2_req_{code.lower()}", role="A")

    res = _request(
        client, f"f2_req_{code.lower()}",
        {"work_date": "2042-04-10", "kind": "change_code", "requested_code": code},
    )

    assert res.status_code == 422, res.text
    assert res.json()["detail"] == _NOT_REQUESTABLE


@pytest.mark.parametrize(("role", "code"), [("T", "AD"), ("A", "A")])
def test_requesting_a_regular_code_is_accepted(client: TestClient, role: str, code: str):
    admin = _bearer(_token(client, "admin", "admin123"))
    username = f"f2_ok_{role.lower()}"
    _create_user(client, admin, username, role=role)

    res = _request(
        client, username,
        {"work_date": "2042-04-11", "kind": "change_code", "requested_code": code},
    )

    assert res.status_code == 201, res.text
    assert res.json()["requested_code"] == code


def test_swap_that_hands_leave_to_the_counterpart_is_refused(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    ids = [_create_user(client, admin, f"f2_swap_a{i}", role="A")["id"] for i in (1, 2, 3, 4)]
    gen = client.post(
        f"{V}/schedules/generate", headers=admin, json={"year": 2042, "month": 5}
    )
    assert gen.status_code == 200 and gen.json()["feasible"] is True, gen.text
    schedule_id = gen.json()["schedule"]["id"]
    day = "2042-05-12"
    res = client.post(
        f"{V}/schedules/{schedule_id}/override", headers=admin,
        json={"user_id": ids[0], "work_date": day, "code": "AL"},
    )
    assert res.status_code == 200, res.text

    def cells() -> dict[int, str]:
        grid = client.get(f"{V}/schedules/2042/5", headers=admin).json()["assignments"]
        return {a["user_id"]: a["code"] for a in grid if a["work_date"] == day}

    before = cells()
    req = _request(
        client, "f2_swap_a1",
        {"work_date": day, "kind": "swap_with", "counterpart_user_id": ids[1]},
    )
    assert req.status_code == 201, req.text

    dec = client.post(
        f"{V}/shift-changes/{req.json()['id']}/decide", headers=admin,
        json={"status": "approved"},
    )

    assert dec.status_code == 422, dec.text
    assert dec.json()["detail"] == _NOT_REQUESTABLE
    assert cells() == before
