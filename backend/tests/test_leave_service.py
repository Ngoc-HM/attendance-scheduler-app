"""Unit + integration tests for F-05/F-06 leave service.

Coverage targets:
- Classification boundary: 5 days → monthly, more than 5 days → annual.
- Monthly window: open days 1–AUTORUN_DAY (20), closed the day after.
- Annual window: prior-year ok, same-year rejected.
- Approve keeps the stored quota; approved_off_map shows AL.
- Annual leave quota: remaining = quota - approved days in the year (D4).
- Overlap guard → 409.
- Conflict ranking by carry_comp.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.models.enums import LeaveStatus, LeaveType
from app.services.leave_conflict_resolver import rank
from app.services.leave_windows import (
    annual_target_year,
    classify,
    is_annual_window_open,
    is_monthly_window_open,
    monthly_target,
)

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

    def test_monthly_window_closes_on_autorun_day(self, monkeypatch):
        """The window's last day is settings.AUTORUN_DAY, not a literal 20."""
        from app.core.config import settings
        from app.services.leave_windows import registration_last_day

        monkeypatch.setattr(settings, "AUTORUN_DAY", 20)
        assert registration_last_day() == 20
        assert is_monthly_window_open(date(2025, 2, 20), target_month=3, target_year=2025)
        assert not is_monthly_window_open(date(2025, 2, 21), target_month=3, target_year=2025)

        monkeypatch.setattr(settings, "AUTORUN_DAY", 15)
        assert registration_last_day() == 15
        assert is_monthly_window_open(date(2025, 2, 15), target_month=3, target_year=2025)
        assert not is_monthly_window_open(date(2025, 2, 16), target_month=3, target_year=2025)

    def test_monthly_target_is_next_month(self):
        assert monthly_target(date(2026, 11, 5)) == (2026, 12)
        # The target stays next month after the window has closed.
        assert monthly_target(date(2026, 11, 25)) == (2026, 12)

    def test_monthly_target_december_rolls_into_january(self):
        assert monthly_target(date(2026, 12, 5)) == (2027, 1)


class TestAnnualWindow:
    def test_year_plus_one_ok(self):
        # Leave starts 2026-06-01; today is 2025-11-01 → Y+1.
        assert is_annual_window_open(date(2025, 11, 1), leave_start_year=2026)

    def test_same_year_rejected(self):
        # Leave starts 2025-06-01; today is 2025-01-01 → not Y+1.
        assert not is_annual_window_open(date(2025, 1, 1), leave_start_year=2025)

    def test_two_years_ahead_rejected(self):
        # Leave starts 2027; today is 2025 → not exactly Y+1.
        assert not is_annual_window_open(date(2025, 6, 1), leave_start_year=2027)

    def test_annual_target_year_is_next_year(self):
        today = date(2026, 11, 5)
        assert annual_target_year(today) == 2027
        assert is_annual_window_open(today, leave_start_year=annual_target_year(today))


class TestConflictRank:
    """Pure ranking logic — no DB needed.

    Uses simple namespace objects to avoid SQLAlchemy ORM instrumentation.
    The rank() function only reads request fields plus the carry_comp map the
    caller derived from schedule_history, so plain objects work perfectly.
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

    def test_higher_carry_comp_ranks_first(self):
        req_a = self._make_req(1, user_id=1, created_offset_days=0)
        req_b = self._make_req(2, user_id=2, created_offset_days=0)
        ranked = rank([req_b, req_a], {1: 3, 2: 0})
        assert ranked[0].user_id == 1  # higher carry_comp first

    def test_equal_carry_comp_tiebreak_by_created_at(self):
        req_a = self._make_req(1, user_id=1, created_offset_days=0)
        req_b = self._make_req(2, user_id=2, created_offset_days=1)
        ranked = rank([req_b, req_a], {1: 2, 2: 2})
        assert ranked[0].id == 1  # earlier created_at wins

    def test_unknown_user_treated_as_zero_comp(self):
        req_a = self._make_req(1, user_id=99)  # user 99 not in map
        req_b = self._make_req(2, user_id=2)
        ranked = rank([req_a, req_b], {2: 1})
        assert ranked[0].user_id == 2  # user_b has carry_comp=1 > 0

    def test_fewer_offs_already_held_in_block_ranks_first(self):
        """Criterion (b): the person with less of their weekly rest entitlement wins."""
        req_a = self._make_req(1, user_id=1)
        req_b = self._make_req(2, user_id=2)
        # User 1 already holds 2 approved offs in the same 7-day block (May 1–7).
        held = {1: {date(2025, 5, 5), date(2025, 5, 6)}, 2: set()}
        ranked = rank([req_a, req_b], {1: 0, 2: 0}, held)
        assert ranked[0].user_id == 2

    def test_weekend_pairing_breaks_ties(self):
        """Criterion (c): Sat+Sun > Fri+Sat > Sun+Mon > no pair."""
        from datetime import datetime
        from types import SimpleNamespace

        def req(id_, user_id, start, end):
            return SimpleNamespace(
                id=id_, user_id=user_id, start_date=start, end_date=end,
                leave_type=LeaveType.monthly, status=LeaveStatus.pending, note=None,
                created_at=datetime(2025, 1, 1),
            )

        sat_sun = req(1, 1, date(2025, 5, 3), date(2025, 5, 4))   # Sat–Sun
        fri_sat = req(2, 2, date(2025, 5, 2), date(2025, 5, 3))   # Fri–Sat
        sun_mon = req(3, 3, date(2025, 5, 4), date(2025, 5, 5))   # Sun–Mon
        midweek = req(4, 4, date(2025, 5, 6), date(2025, 5, 7))   # Tue–Wed
        carry = {i: 0 for i in range(1, 5)}
        ranked = rank([midweek, sun_mon, fri_sat, sat_sun], carry)
        assert [r.id for r in ranked] == [1, 2, 3, 4]


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
        json={
            "username": username, "full_name": username.title(),
            "password": "secret1", "role": role,
        },
    )


class TestLeaveEndpoints:
    """Integration tests requiring the HTTP client fixture."""

    def _admin_headers(self, client):
        return _bearer(_token(client, "admin", "admin123"))

    def test_dev_mode_bypasses_registration_window(self, client: TestClient):
        """Development supports immediate end-to-end testing on any date."""
        from app.core.database import get_db
        from app.schemas.leave import LeaveCreate
        from app.services import leave_service

        admin = self._admin_headers(client)
        uid = _create_user(client, admin, "dev_window_bypass").json()["id"]
        db_gen = get_db()
        db = next(db_gen)
        try:
            request = leave_service.create_request(
                db,
                uid,
                LeaveCreate(
                    start_date=date(2033, 9, 3),
                    end_date=date(2033, 9, 4),
                ),
                today=date(2026, 7, 22),
            )
            assert request.status is LeaveStatus.pending
        finally:
            db.close()

    def test_approve_within_quota_keeps_quota(self, client: TestClient):
        """Approving within the quota warns nothing; the stored quota is never
        decremented (the remaining balance is derived from approved leave)."""
        admin = self._admin_headers(client)

        # Create user.
        r = _create_user(client, admin, "bal_user_leave")
        assert r.status_code == 201
        uid = r.json()["id"]

        from app.core.database import get_db
        from app.models.user import User
        from app.schemas.leave import LeaveCreate
        from app.services import leave_service

        db_gen = get_db()
        db = next(db_gen)
        try:
            # Set the quota to 10 directly via DB.
            user = db.get(User, uid)
            user.annual_leave_quota = 10
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
            req_approved, warnings = leave_service.decide(
                db, leave_id, LeaveStatus.approved, admin_id=1
            )
            assert req_approved.status == LeaveStatus.approved
            assert warnings == []

            db.refresh(user)
            assert user.annual_leave_quota == 10
        finally:
            db.close()

    def test_approved_off_map_shows_al(self, client: TestClient):
        """approved_off_map includes AL for approved leave days in that month."""
        from app.core.database import get_db
        from app.models.enums import AttendanceCode
        from app.schemas.leave import LeaveCreate
        from app.services import leave_service

        admin = self._admin_headers(client)
        r = _create_user(client, admin, "map_user_leave")
        uid = r.json()["id"]

        db_gen = get_db()
        db = next(db_gen)
        try:
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
        from app.schemas.leave import LeaveCreate
        from app.services import leave_service

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
        from fastapi import HTTPException

        from app.core.database import get_db
        from app.schemas.leave import LeaveCreate
        from app.services import leave_service

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
                leave_service.create_request(
                    db, uid, payload, today=today, enforce_window=True
                )
            assert exc_info.value.status_code == 400
        finally:
            db.close()

    def test_conflicts_rank_by_carry_from_schedule_history(self, client: TestClient):
        """B6: conflict ranking reads carry_comp from history, not the stored column."""
        from app.core.database import SessionLocal
        from app.models.leave import LeaveRequest

        admin = self._admin_headers(client)
        early = _create_user(client, admin, "conflict_early").json()["id"]
        owed = _create_user(client, admin, "conflict_owed").json()["id"]
        # One A/D the month before earns a comp day that no month-close has
        # persisted yet, so users.carry_comp is still 0 for both.
        client.put(
            f"{V}/attendance", headers=admin,
            json={"user_id": owed, "work_date": "2031-02-10", "code": "A/D"},
        )

        db = SessionLocal()
        try:
            for uid in (early, owed):  # `early` submits first
                db.add(LeaveRequest(
                    user_id=uid, start_date=date(2031, 3, 10),
                    end_date=date(2031, 3, 10), leave_type=LeaveType.monthly,
                ))
                db.flush()
            db.commit()
        finally:
            db.close()

        res = client.get(
            f"{V}/leaves/conflicts", headers=admin, params={"date": "2031-03-10"}
        )
        assert res.status_code == 200
        assert [e["user_id"] for e in res.json()] == [owed, early]

# ---------------------------------------------------------------------------
# B3 — caller-supplied leave_type must match the span (> 5 days is annual)
# ---------------------------------------------------------------------------

_TYPE_SPAN_MISMATCH = (
    "Leave of 5 days or less is monthly leave; more than 5 consecutive days "
    "must be registered as annual leave."
)


def _post_leave_as_new_user(client, username, start, end, leave_type):
    admin = _bearer(_token(client, "admin", "admin123"))
    assert _create_user(client, admin, username).status_code == 201
    user = _bearer(_token(client, username, "secret1"))
    return client.post(
        f"{V}/leaves",
        headers=user,
        json={
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "leave_type": leave_type,
        },
    )


def test_monthly_label_on_long_span_rejected(client):
    # 10 consecutive days labelled monthly would bypass the annual rule.
    r = _post_leave_as_new_user(
        client, "b3_long_monthly", date(2033, 6, 1), date(2033, 6, 10), "monthly"
    )
    assert r.status_code == 422
    assert r.json()["detail"] == _TYPE_SPAN_MISMATCH


def test_annual_label_on_short_span_rejected(client):
    r = _post_leave_as_new_user(
        client, "b3_short_annual", date(2033, 7, 1), date(2033, 7, 3), "annual"
    )
    assert r.status_code == 422
    assert r.json()["detail"] == _TYPE_SPAN_MISMATCH


def test_matching_label_accepted(client):
    r = _post_leave_as_new_user(
        client, "b3_short_monthly", date(2033, 8, 1), date(2033, 8, 3), "monthly"
    )
    assert r.status_code == 201
    assert r.json()["leave_type"] == "monthly"

class TestWindowBusinessClock:
    """The window is judged on the Frankfurt business date, not the host's."""

    def test_window_uses_business_timezone_date(self, client: TestClient, monkeypatch):
        from datetime import UTC, datetime

        from fastapi import HTTPException

        from app.core import business_time
        from app.core.config import settings
        from app.core.database import get_db
        from app.schemas.leave import LeaveCreate
        from app.services import leave_service

        monkeypatch.setattr(settings, "AUTORUN_DAY", 20)
        monkeypatch.setattr(settings, "TIMEZONE", "Europe/Berlin")
        admin = _bearer(_token(client, "admin", "admin123"))
        uid = _create_user(client, admin, "window_business_clock").json()["id"]

        db = next(get_db())
        try:
            # 22:30 UTC = 23:30 Berlin on 2026-12-20: still the last open day.
            monkeypatch.setattr(
                business_time, "_utcnow",
                lambda: datetime(2026, 12, 20, 22, 30, tzinfo=UTC),
            )
            accepted = leave_service.create_request(
                db, uid,
                LeaveCreate(start_date=date(2027, 1, 4), end_date=date(2027, 1, 5)),
                enforce_window=True,
            )
            assert accepted.status is LeaveStatus.pending

            # 23:30 UTC = 00:30 Berlin on 2026-12-21: closed (draft is due at 00:05).
            monkeypatch.setattr(
                business_time, "_utcnow",
                lambda: datetime(2026, 12, 20, 23, 30, tzinfo=UTC),
            )
            with pytest.raises(HTTPException) as exc_info:
                leave_service.create_request(
                    db, uid,
                    LeaveCreate(start_date=date(2027, 1, 11), end_date=date(2027, 1, 12)),
                    enforce_window=True,
                )
            assert exc_info.value.status_code == 400
        finally:
            db.close()

    def test_window_closed_message_names_autorun_day(self, client: TestClient, monkeypatch):
        from fastapi import HTTPException

        from app.core.config import settings
        from app.core.database import get_db
        from app.schemas.leave import LeaveCreate
        from app.services import leave_service

        monkeypatch.setattr(settings, "AUTORUN_DAY", 15)
        admin = _bearer(_token(client, "admin", "admin123"))
        uid = _create_user(client, admin, "window_message_day").json()["id"]

        db = next(get_db())
        try:
            with pytest.raises(HTTPException) as exc_info:
                leave_service.create_request(
                    db, uid,
                    LeaveCreate(start_date=date(2025, 3, 3), end_date=date(2025, 3, 4)),
                    today=date(2025, 2, 16),
                    enforce_window=True,
                )
            assert exc_info.value.status_code == 400
            assert "day 15" in exc_info.value.detail
        finally:
            db.close()


def test_leave_window_status(client: TestClient, monkeypatch) -> None:
    """Window is open days 1–AUTORUN_DAY for next month; dev never closes it."""
    from app.core.config import settings
    from app.services import leave_service
    from app.services.leave_windows import registration_last_day

    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "AUTORUN_DAY", 20)

    day5 = leave_service.window_status(today=date(2026, 11, 5))
    assert day5.monthly_open is True
    assert (day5.monthly_target_year, day5.monthly_target_month) == (2026, 12)
    assert day5.annual_target_year == 2027
    assert day5.closes_on_day == registration_last_day() == 20
    assert day5.enforced is True

    # Boundary: the last registration day is open, the next day is closed.
    assert leave_service.window_status(today=date(2026, 11, 20)).monthly_open is True
    assert leave_service.window_status(today=date(2026, 11, 21)).monthly_open is False
    assert leave_service.window_status(today=date(2026, 11, 25)).monthly_open is False

    # Dev does not enforce the window, so registration is always open.
    monkeypatch.setattr(settings, "ENVIRONMENT", "dev")
    dev = leave_service.window_status(today=date(2026, 11, 25))
    assert dev.enforced is False
    assert dev.monthly_open is True

    # Wiring: any signed-in active user (not only admin) can read it.
    admin = _bearer(_token(client, "admin", "admin123"))
    _create_user(client, admin, "window_status_user")
    employee = _bearer(_token(client, "window_status_user", "secret1"))
    r = client.get(f"{V}/leaves/window", headers=employee)
    assert r.status_code == 200
    assert set(r.json()) == {
        "monthly_open", "monthly_target_year", "monthly_target_month",
        "annual_target_year", "closes_on_day", "enforced",
    }
    assert r.json()["enforced"] is False
    assert r.json()["monthly_open"] is True


def test_leave_window_status_uses_business_date(monkeypatch) -> None:
    """Without an explicit date, the window is judged on the Frankfurt date."""
    from datetime import UTC, datetime

    from app.core import business_time
    from app.core.config import settings
    from app.services import leave_service

    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "AUTORUN_DAY", 20)
    monkeypatch.setattr(settings, "TIMEZONE", "Europe/Berlin")

    # 22:30 UTC = 23:30 Berlin on 2026-12-20: last open day for January.
    monkeypatch.setattr(
        business_time, "_utcnow", lambda: datetime(2026, 12, 20, 22, 30, tzinfo=UTC)
    )
    still_open = leave_service.window_status()
    assert (still_open.monthly_target_year, still_open.monthly_target_month) == (2027, 1)
    assert still_open.monthly_open is True

    # 23:30 UTC = 00:30 Berlin on 2026-12-21: closed.
    monkeypatch.setattr(
        business_time, "_utcnow", lambda: datetime(2026, 12, 20, 23, 30, tzinfo=UTC)
    )
    assert leave_service.window_status().monthly_open is False


# ---------------------------------------------------------------------------
# Annual leave quota and remaining balance (owner decision D4, 2026-11-06)
# ---------------------------------------------------------------------------

def _leave(db, user_id, start, end):
    from app.schemas.leave import LeaveCreate
    from app.services import leave_service

    return leave_service.create_request(
        db, user_id, LeaveCreate(start_date=start, end_date=end), enforce_window=False
    )


def test_annual_leave_summary_counts_approved_days_in_year(client: TestClient) -> None:
    """quota 30; approved 3 days; pending 2 days → used 3, pending 2, remaining 27."""
    from app.core.database import get_db
    from app.services import leave_balance, leave_service

    admin = _bearer(_token(client, "admin", "admin123"))
    uid = _create_user(client, admin, "d4_summary_user", role="T").json()["id"]
    db = next(get_db())
    try:
        approved = _leave(db, uid, date(2040, 12, 20), date(2040, 12, 22))
        leave_service.decide(db, approved.id, LeaveStatus.approved, admin_id=1)
        _leave(db, uid, date(2040, 12, 27), date(2040, 12, 28))  # stays pending
        rejected = _leave(db, uid, date(2040, 11, 5), date(2040, 11, 6))
        leave_service.decide(db, rejected.id, LeaveStatus.rejected, admin_id=1)

        summary = leave_balance.annual_leave_summary(db, uid, 2040)
        assert (
            summary.year, summary.quota, summary.used, summary.pending, summary.remaining
        ) == (2040, 30, 3, 2, 27)

        # A leave across New Year counts only its days inside each year.
        across = _leave(db, uid, date(2040, 12, 30), date(2041, 1, 2))
        leave_service.decide(db, across.id, LeaveStatus.approved, admin_id=1)
        assert leave_balance.annual_leave_summary(db, uid, 2040).used == 5
        assert leave_balance.annual_leave_summary(db, uid, 2041).used == 2
    finally:
        db.close()


def test_approve_beyond_annual_quota_warns(client: TestClient) -> None:
    """Going past the quota is allowed (admin decides) but warns; reaching it does not."""
    from app.core.database import get_db
    from app.core.i18n import t
    from app.services import leave_service

    admin = _bearer(_token(client, "admin", "admin123"))
    uid = _create_user(client, admin, "d4_quota_warn_user", role="T").json()["id"]
    assert client.patch(
        f"{V}/users/{uid}", headers=admin, json={"annual_leave_quota": 5}
    ).status_code == 200
    exceeded = t("leave.balance_exceeded", "en")
    assert exceeded == "Approving exceeds this person's annual leave quota."
    db = next(get_db())
    try:
        first = _leave(db, uid, date(2040, 3, 5), date(2040, 3, 7))  # 3 of 5
        _, warnings = leave_service.decide(db, first.id, LeaveStatus.approved, admin_id=1)
        assert exceeded not in warnings

        exact = _leave(db, uid, date(2040, 4, 2), date(2040, 4, 3))  # 5 of 5
        _, warnings = leave_service.decide(db, exact.id, LeaveStatus.approved, admin_id=1)
        assert exceeded not in warnings

        over = _leave(db, uid, date(2040, 5, 7), date(2040, 5, 7))  # 6 of 5
        decided, warnings = leave_service.decide(
            db, over.id, LeaveStatus.approved, admin_id=1
        )
        assert decided.status is LeaveStatus.approved
        assert exceeded in warnings
    finally:
        db.close()


def test_balance_endpoint_self_and_admin(client: TestClient) -> None:
    """Own balance 200; someone else's 403; admin may read anyone's."""
    from app.core.business_time import business_today

    admin = _bearer(_token(client, "admin", "admin123"))
    me_id = _create_user(client, admin, "d4_balance_self", role="T").json()["id"]
    other_id = _create_user(client, admin, "d4_balance_other", role="T").json()["id"]
    me = _bearer(_token(client, "d4_balance_self", "secret1"))

    own = client.get(f"{V}/leaves/balance", headers=me, params={"year": 2040})
    assert own.status_code == 200
    assert own.json() == {
        "year": 2040, "quota": 30, "used": 0, "pending": 0, "remaining": 30,
    }
    explicit = client.get(
        f"{V}/leaves/balance", headers=me, params={"user_id": me_id, "year": 2040}
    )
    assert explicit.json() == own.json()

    # Defaults: the caller's own balance for the current business year.
    default = client.get(f"{V}/leaves/balance", headers=me)
    assert default.status_code == 200
    assert default.json()["year"] == business_today().year

    forbidden = client.get(
        f"{V}/leaves/balance", headers=me, params={"user_id": other_id}
    )
    assert forbidden.status_code == 403

    as_admin = client.get(
        f"{V}/leaves/balance", headers=admin, params={"user_id": other_id, "year": 2040}
    )
    assert as_admin.status_code == 200
    assert as_admin.json()["remaining"] == 30
    assert client.get(
        f"{V}/leaves/balance", headers=admin, params={"user_id": 999_999}
    ).status_code == 404
