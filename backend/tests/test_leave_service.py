"""Unit + integration tests for F-05/F-06 leave service.

Coverage targets:
- Classification boundary: 4 days → monthly, 5 days → annual.
- Monthly window: open days 1–20, closed day 21.
- Annual window: prior-year ok, same-year rejected.
- Approve decrements annual_leave_balance; approved_off_map shows AL.
- Overlap guard → 409.
- Conflict ranking by carry_comp.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.models.enums import LeaveStatus, LeaveType
from app.services.leave_windows import classify, is_annual_window_open, is_monthly_window_open
from app.services.leave_conflict_resolver import rank

V = "/api/v1"


# ---------------------------------------------------------------------------
# Pure unit tests (no DB)
# ---------------------------------------------------------------------------

class TestClassify:
    def test_four_days_is_monthly(self):
        start = date(2025, 3, 10)
        end = date(2025, 3, 13)  # inclusive span = 4
        assert classify(start, end) is LeaveType.monthly

    def test_five_days_is_monthly(self):
        # Customer rule 2026-06-12: only MORE than 5 days (>=6) is annual.
        start = date(2025, 3, 10)
        end = date(2025, 3, 14)  # inclusive span = 5
        assert classify(start, end) is LeaveType.monthly

    def test_one_day_is_monthly(self):
        d = date(2025, 4, 1)
        assert classify(d, d) is LeaveType.monthly

    def test_six_days_is_annual(self):
        start = date(2025, 6, 1)
        end = date(2025, 6, 6)  # inclusive span = 6
        assert classify(start, end) is LeaveType.annual


class TestMonthlyWindow:
    def test_open_day_1(self):
        # Registering for March 2025 → window is Feb 1–20.
        assert is_monthly_window_open(date(2025, 2, 1), target_month=3, target_year=2025)

    def test_open_day_20(self):
        assert is_monthly_window_open(date(2025, 2, 20), target_month=3, target_year=2025)

    def test_closed_day_21(self):
        assert not is_monthly_window_open(date(2025, 2, 21), target_month=3, target_year=2025)

    def test_closed_wrong_month(self):
        # Submitting in March for March (same month) is not the prior month.
        assert not is_monthly_window_open(date(2025, 3, 5), target_month=3, target_year=2025)

    def test_open_january_target_uses_december(self):
        # Registering for Jan 2026 → window is Dec 1–20 2025.
        assert is_monthly_window_open(date(2025, 12, 15), target_month=1, target_year=2026)

    def test_closed_january_target_wrong_year(self):
        assert not is_monthly_window_open(date(2026, 1, 5), target_month=1, target_year=2026)


class TestAnnualWindow:
    def test_prior_year_ok(self):
        # Leave starts 2026-06-01; today is 2025-11-01 → prior year.
        assert is_annual_window_open(date(2025, 11, 1), leave_start_year=2026)

    def test_same_year_rejected(self):
        # Leave starts 2025-06-01; today is 2025-01-01 → same year.
        assert not is_annual_window_open(date(2025, 1, 1), leave_start_year=2025)

    def test_two_years_ahead_rejected(self):
        # Leave starts 2027; today is 2025 → too early (must be year-1).
        assert not is_annual_window_open(date(2025, 6, 1), leave_start_year=2027)


class TestConflictRank:
    """Pure ranking logic — no DB needed.

    Uses simple namespace objects to avoid SQLAlchemy ORM instrumentation.
    The rank() function only reads .id, .user_id, and .created_at — no ORM
    operations, so plain objects work perfectly.
    """

    def _make_req(self, id_, user_id, created_offset_days=0):
        from datetime import datetime
        from types import SimpleNamespace
        return SimpleNamespace(
            id=id_,
            user_id=user_id,
            start_date=date(2025, 5, 1),
            end_date=date(2025, 5, 3),
            leave_type=LeaveType.monthly,
            status=LeaveStatus.pending,
            note=None,
            created_at=datetime(2025, 1, 1) + timedelta(days=created_offset_days),
        )

    def _make_user(self, id_, carry_comp):
        from types import SimpleNamespace
        return SimpleNamespace(id=id_, carry_comp=carry_comp)

    def test_higher_carry_comp_ranks_first(self):
        req_a = self._make_req(1, user_id=1, created_offset_days=0)
        req_b = self._make_req(2, user_id=2, created_offset_days=0)
        user_a = self._make_user(1, carry_comp=3)
        user_b = self._make_user(2, carry_comp=1)
        ranked = rank([req_b, req_a], {1: user_a, 2: user_b})
        assert ranked[0].user_id == 1  # higher carry_comp first

    def test_equal_carry_comp_tiebreak_by_created_at(self):
        req_a = self._make_req(1, user_id=1, created_offset_days=0)
        req_b = self._make_req(2, user_id=2, created_offset_days=1)
        user_a = self._make_user(1, carry_comp=2)
        user_b = self._make_user(2, carry_comp=2)
        ranked = rank([req_b, req_a], {1: user_a, 2: user_b})
        assert ranked[0].id == 1  # earlier created_at wins

    def test_unknown_user_treated_as_zero_comp(self):
        req_a = self._make_req(1, user_id=99)  # user 99 not in map
        req_b = self._make_req(2, user_id=2)
        user_b = self._make_user(2, carry_comp=1)
        ranked = rank([req_a, req_b], {2: user_b})
        assert ranked[0].user_id == 2  # user_b has carry_comp=1 > 0


# ---------------------------------------------------------------------------
# Integration tests (via HTTP client + SQLite in-memory)
# ---------------------------------------------------------------------------

def _login(client, username, password):
    return client.post(f"{V}/auth/login", data={"username": username, "password": password})


def _token(client, username, password):
    return _login(client, username, password).json()["access_token"]


def _bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


def _create_user(client, admin_headers, username, role="A"):
    return client.post(
        f"{V}/users",
        headers=admin_headers,
        json={"username": username, "full_name": username.title(), "password": "secret1", "role": role},
    )


class TestLeaveEndpoints:
    """Integration tests requiring the HTTP client fixture."""

    def _admin_headers(self, client):
        return _bearer(_token(client, "admin", "admin123"))

    def test_approve_decrements_balance(self, client: TestClient):
        """Approving a leave request reduces annual_leave_balance by day count."""
        admin = self._admin_headers(client)

        # Create user.
        r = _create_user(client, admin, "bal_user_leave")
        assert r.status_code == 201
        uid = r.json()["id"]

        from app.core.database import get_db
        from app.services import leave_service
        from app.schemas.leave import LeaveCreate
        from app.models.user import User

        db_gen = get_db()
        db = next(db_gen)
        try:
            # Set balance to 10 directly via DB.
            user = db.get(User, uid)
            user.annual_leave_balance = 10
            db.commit()

            # Window: submitting on day 10 of month M for month M+1.
            today = date(2025, 2, 10)
            payload = LeaveCreate(
                start_date=date(2025, 3, 3),
                end_date=date(2025, 3, 5),  # 3 days → monthly
                note="test",
            )
            req = leave_service.create_request(db, uid, payload, today=today)
            leave_id = req.id

            # Admin approves.
            req_approved = leave_service.decide(db, leave_id, LeaveStatus.approved, admin_id=1)
            assert req_approved.status == LeaveStatus.approved

            # Balance reduced by 3.
            db.refresh(user)
            assert user.annual_leave_balance == 7
        finally:
            db.close()

    def test_approved_off_map_shows_al(self, client: TestClient):
        """approved_off_map includes AL for approved leave days in that month."""
        from app.core.database import get_db
        from app.services import leave_service
        from app.schemas.leave import LeaveCreate
        from app.models.enums import AttendanceCode
        from app.models.user import User

        admin = self._admin_headers(client)
        r = _create_user(client, admin, "map_user_leave")
        uid = r.json()["id"]

        db_gen = get_db()
        db = next(db_gen)
        try:
            # Set balance via DB directly.
            user = db.get(User, uid)
            user.annual_leave_balance = 20
            db.commit()

            today = date(2025, 2, 5)
            payload = LeaveCreate(
                start_date=date(2025, 3, 10),
                end_date=date(2025, 3, 12),  # 3 days → monthly
            )
            req = leave_service.create_request(db, uid, payload, today=today)
            leave_service.decide(db, req.id, LeaveStatus.approved, admin_id=1)

            off_map = leave_service.approved_off_map(db, 2025, 3)
            assert uid in off_map
            assert off_map[uid][date(2025, 3, 10)] == AttendanceCode.AL
            assert off_map[uid][date(2025, 3, 11)] == AttendanceCode.AL
            assert off_map[uid][date(2025, 3, 12)] == AttendanceCode.AL
        finally:
            db.close()

    def test_overlap_returns_409(self, client: TestClient):
        """Submitting an overlapping leave request returns 409."""
        from app.core.database import get_db
        from app.main import app
        from app.services import leave_service
        from app.schemas.leave import LeaveCreate

        admin = self._admin_headers(client)
        r = _create_user(client, admin, "overlap_user_leave")
        uid = r.json()["id"]

        db_gen = get_db()
        db = next(db_gen)
        try:
            today = date(2025, 2, 5)
            payload = LeaveCreate(
                start_date=date(2025, 3, 10),
                end_date=date(2025, 3, 12),
            )
            leave_service.create_request(db, uid, payload, today=today)

            # Same range again → overlap.
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                leave_service.create_request(db, uid, payload, today=today)
            assert exc_info.value.status_code == 409
        finally:
            db.close()

    def test_window_closed_day_21(self, client: TestClient):
        """Submitting monthly leave on day 21 raises 400 window_closed."""
        from app.core.database import get_db
        from app.services import leave_service
        from app.schemas.leave import LeaveCreate
        from fastapi import HTTPException

        admin = self._admin_headers(client)
        r = _create_user(client, admin, "window_user_leave")
        uid = r.json()["id"]

        db_gen = get_db()
        db = next(db_gen)
        try:
            # Day 21 — window is closed.
            today = date(2025, 2, 21)
            payload = LeaveCreate(
                start_date=date(2025, 3, 3),
                end_date=date(2025, 3, 5),
            )
            with pytest.raises(HTTPException) as exc_info:
                leave_service.create_request(db, uid, payload, today=today)
            assert exc_info.value.status_code == 400
        finally:
            db.close()
