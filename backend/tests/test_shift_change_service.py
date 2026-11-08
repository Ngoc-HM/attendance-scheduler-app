"""Unit + integration tests for shift-change request service (decision #8, spec §3).

Coverage targets:
- create own-cell ok; no own cell → 409; AL/CD cell → 422 (create + approval).
- swap partner: unknown → 404; self / other codes / inactive → 422.
- a second approve → 409, the swap applied once.
- missing requested_code for change_code kind → 400.
- missing counterpart_user_id for swap_with kind → 400.
- strict_review true for A role, false for T role.
- decide approve with no schedule for the month → 409, request stays pending.
- re-decide → 409.
- a swap that would hand leave (AL) to the counterpart → 422 at approval.
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
        _give_cell(uid, date(2061, 4, 10), "A")

        db = _get_db()
        try:
            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2061, 4, 10),
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
        _give_cell(uid, date(2061, 4, 15), "A")

        db = _get_db()
        try:
            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2061, 4, 15),
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
        _give_cell(uid, date(2061, 4, 15), "AD")

        db = _get_db()
        try:
            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2061, 4, 15),
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.X,
            )
            _, strict_review = shift_change_service.create_request(db, uid, payload)
            assert strict_review is False
        finally:
            db.close()

    def test_decide_approve_without_schedule_raises_409(self, client: TestClient):
        """Phase 05: approving a change with NO schedule for that month is an
        error (409 swap.no_schedule) — there is nothing to apply it to.

        Creation now refuses such a request, so the row is written directly:
        an old request filed before that check existed."""
        admin = self._admin_headers(client)
        user = _create_user(client, admin, "sc_approve_warn", role="A")
        uid = user["id"]

        db = _get_db()
        try:
            from app.models.enums import AttendanceCode
            from app.models.shift_change_request import ShiftChangeRequest
            from app.services import shift_change_service

            req = ShiftChangeRequest(
                requester_id=uid,
                work_date=date(2068, 4, 20),  # no schedule covers 2068
                kind=SwapKind.change_code,
                requested_code=AttendanceCode.A,
                status=LeaveStatus.pending,
            )
            db.add(req)
            db.commit()
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
        _give_cell(uid, date(2061, 4, 22), "A")

        db = _get_db()
        try:
            from fastapi import HTTPException

            from app.models.enums import AttendanceCode
            from app.schemas.shift_change import ShiftChangeCreate
            from app.services import shift_change_service

            payload = ShiftChangeCreate(
                work_date=date(2061, 4, 22),
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
    uid = _create_user(client, admin, username, role=role)["id"]
    _give_cell(uid, date(2061, 4, 11), "X")

    res = _request(
        client, username,
        {"work_date": "2061-04-11", "kind": "change_code", "requested_code": code},
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


# ---------------------------------------------------------------------------
# Review 2 (B4, E): create-time validation, locked cells, double approve.
# Cells are written straight into a 2061 draft schedule (no other test uses
# that year), so each test owns its people's cells without running the engine.
# ---------------------------------------------------------------------------

_CELL_LOCKED = (
    "Leave, comp, sick and admin-assigned days cannot be changed by request"
    " — only regular working or off days."
)


def _give_cell(user_id: int, day: date, code: str) -> None:
    """Put ``code`` into ``user_id``'s planned cell on ``day`` (draft month)."""
    from app.core.database import SessionLocal
    from app.models.enums import AttendanceCode, ScheduleStatus
    from app.models.schedule import MonthlySchedule, ShiftAssignment

    db = SessionLocal()
    try:
        schedule = (
            db.query(MonthlySchedule)
            .filter_by(year=day.year, month=day.month)
            .one_or_none()
        )
        if schedule is None:
            schedule = MonthlySchedule(
                year=day.year, month=day.month, status=ScheduleStatus.draft
            )
            db.add(schedule)
            db.flush()
        cell = (
            db.query(ShiftAssignment)
            .filter_by(schedule_id=schedule.id, user_id=user_id, work_date=day)
            .one_or_none()
        )
        if cell is None:
            db.add(
                ShiftAssignment(
                    schedule_id=schedule.id, user_id=user_id, work_date=day,
                    code=AttendanceCode(code),
                )
            )
        else:
            cell.code = AttendanceCode(code)
        db.commit()
    finally:
        db.close()


def _cell(user_id: int, day: date) -> str:
    from app.core.database import SessionLocal
    from app.models.schedule import ShiftAssignment

    db = SessionLocal()
    try:
        cell = db.query(ShiftAssignment).filter_by(user_id=user_id, work_date=day).one()
        return cell.code.value
    finally:
        db.close()


def _decide(client, admin, req_id, decision="approved"):
    return client.post(
        f"{V}/shift-changes/{req_id}/decide", headers=admin, json={"status": decision}
    )


def test_change_code_on_al_cell_refused(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    uid = _create_user(client, admin, "r2_al_cell", role="A")["id"]
    day = date(2061, 3, 10)
    _give_cell(uid, day, "AL")

    res = _request(
        client, "r2_al_cell",
        {"work_date": day.isoformat(), "kind": "change_code", "requested_code": "A"},
    )
    assert res.status_code == 422, res.text
    assert res.json()["detail"] == _CELL_LOCKED

    # An older pending request (filed while the cell was still a working
    # day) is refused at approval once the cell turned into leave.
    later = date(2061, 3, 11)
    _give_cell(uid, later, "D")
    req = _request(
        client, "r2_al_cell",
        {"work_date": later.isoformat(), "kind": "change_code", "requested_code": "X"},
    )
    assert req.status_code == 201, req.text
    _give_cell(uid, later, "AL")

    dec = _decide(client, admin, req.json()["id"])

    assert dec.status_code == 422, dec.text
    assert dec.json()["detail"] == _CELL_LOCKED
    assert _cell(uid, later) == "AL"


def test_change_code_on_cd_cell_refused(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    uid = _create_user(client, admin, "r2_cd_cell", role="T")["id"]
    day = date(2061, 3, 12)
    _give_cell(uid, day, "CD")

    res = _request(
        client, "r2_cd_cell",
        {"work_date": day.isoformat(), "kind": "change_code", "requested_code": "AD"},
    )

    assert res.status_code == 422, res.text
    assert res.json()["detail"] == _CELL_LOCKED
    assert _cell(uid, day) == "CD"


def test_create_swap_unknown_counterpart_404(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    _create_user(client, admin, "r2_swap_ghost", role="A")

    res = _request(
        client, "r2_swap_ghost",
        {"work_date": "2061-03-13", "kind": "swap_with", "counterpart_user_id": 987654},
    )

    assert res.status_code == 404, res.text
    assert res.json()["detail"] == "User not found."


def test_create_swap_with_self_422(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    uid = _create_user(client, admin, "r2_swap_self", role="A")["id"]

    res = _request(
        client, "r2_swap_self",
        {"work_date": "2061-03-13", "kind": "swap_with", "counterpart_user_id": uid},
    )

    assert res.status_code == 422, res.text
    assert res.json()["detail"] == "You cannot swap a shift with yourself."


def test_create_swap_other_role_422(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    _create_user(client, admin, "r2_swap_role_a", role="A")
    other = _create_user(client, admin, "r2_swap_role_t", role="T")["id"]

    res = _request(
        client, "r2_swap_role_a",
        {"work_date": "2061-03-13", "kind": "swap_with", "counterpart_user_id": other},
    )

    assert res.status_code == 422, res.text
    assert res.json()["detail"] == (
        "You can only swap with a colleague who works the same shift codes."
    )


def test_create_swap_disabled_counterpart_422(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    _create_user(client, admin, "r2_swap_live", role="A")
    gone = _create_user(client, admin, "r2_swap_gone", role="A")["id"]
    off = client.patch(f"{V}/users/{gone}", headers=admin, json={"status": "disabled"})
    assert off.status_code == 200, off.text

    res = _request(
        client, "r2_swap_live",
        {"work_date": "2061-03-13", "kind": "swap_with", "counterpart_user_id": gone},
    )

    assert res.status_code == 422, res.text
    assert res.json()["detail"] == "That colleague's account is not active."


def test_create_request_without_own_cell_409(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    _create_user(client, admin, "r2_no_cell", role="A")

    # 2069: no schedule in the suite ever covers that year.
    res = _request(
        client, "r2_no_cell",
        {"work_date": "2069-06-10", "kind": "change_code", "requested_code": "X"},
    )

    assert res.status_code == 409, res.text
    assert res.json()["detail"] == (
        "You can only request changes for your own scheduled day."
    )


def test_second_approve_is_409(client: TestClient):
    admin = _bearer(_token(client, "admin", "admin123"))
    me = _create_user(client, admin, "r2_double_a1", role="A")["id"]
    you = _create_user(client, admin, "r2_double_a2", role="A")["id"]
    day = date(2061, 3, 14)
    _give_cell(me, day, "A")
    _give_cell(you, day, "X")
    req = _request(
        client, "r2_double_a1",
        {"work_date": day.isoformat(), "kind": "swap_with", "counterpart_user_id": you},
    )
    assert req.status_code == 201, req.text

    first = _decide(client, admin, req.json()["id"])
    assert first.status_code == 200, first.text
    second = _decide(client, admin, req.json()["id"])

    assert second.status_code == 409, second.text
    assert second.json()["detail"] == "This shift-change request was already decided."
    # Swapped exactly once — a second application would swap them back.
    assert (_cell(me, day), _cell(you, day)) == ("X", "A")
