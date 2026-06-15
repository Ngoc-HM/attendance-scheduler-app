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
        json={"username": username, "full_name": username.title(), "password": "secret1", "role": role},
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
            from app.services import shift_change_service
            from app.schemas.shift_change import ShiftChangeCreate
            from app.models.enums import AttendanceCode

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
            from app.services import shift_change_service
            from app.schemas.shift_change import ShiftChangeCreate
            from fastapi import HTTPException

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
            from app.services import shift_change_service
            from app.schemas.shift_change import ShiftChangeCreate
            from fastapi import HTTPException

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
            from app.services import shift_change_service
            from app.schemas.shift_change import ShiftChangeCreate
            from app.models.enums import AttendanceCode

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
            from app.services import shift_change_service
            from app.schemas.shift_change import ShiftChangeCreate
            from app.models.enums import AttendanceCode

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
            from app.services import shift_change_service
            from app.schemas.shift_change import ShiftChangeCreate
            from app.models.enums import AttendanceCode

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 20),
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.A,
            )
            req, _ = shift_change_service.create_request(db, uid, payload)
            admin_user = db.query(__import__("app.models.user", fromlist=["User"]).User).filter_by(username="admin").first()

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
            from app.services import shift_change_service
            from app.schemas.shift_change import ShiftChangeCreate
            from app.models.enums import AttendanceCode
            from fastapi import HTTPException

            payload = ShiftChangeCreate(
                work_date=date(2025, 4, 22),
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.D,
            )
            req, _ = shift_change_service.create_request(db, uid, payload)
            admin_user = db.query(__import__("app.models.user", fromlist=["User"]).User).filter_by(username="admin").first()

            # First decision succeeds (reject needs no schedule to apply to).
            shift_change_service.decide(db, req.id, LeaveStatus.rejected, admin_id=admin_user.id)

            # Second decision on same request → 409.
            with pytest.raises(HTTPException) as exc_info:
                shift_change_service.decide(db, req.id, LeaveStatus.approved, admin_id=admin_user.id)
            assert exc_info.value.status_code == 409
        finally:
            db.close()
