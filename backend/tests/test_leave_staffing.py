"""Flight-staffing risk kept on a leave's row (owner request 2026-11-10).

The admin's leave list carries, per pending/approved request of a role-A
person, the days its absence leaves a flight shift short: from the roster
when the month is generated, otherwise a head count. Approving returns the
same lines.

The rule tests run on their own in-memory database so the head counts do
not depend on the role-A people other tests create; the endpoint tests use
the shared client with a hand-made roster in 2047 that no other test touches.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, SessionLocal
from app.core.i18n import set_request_language
from app.models.enums import (
    AttendanceCode,
    LeaveStatus,
    LeaveType,
    Role,
    ScheduleStatus,
    UserStatus,
)
from app.models.flight import FlightDay
from app.models.leave import LeaveRequest
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.services import leave_service, leave_staffing

V = "/api/v1"
A, D, AD, X, CD, AL = (
    AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D, AttendanceCode.X,
    AttendanceCode.CD, AttendanceCode.AL,
)


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def _english() -> Iterator[None]:
    set_request_language("en")
    yield
    set_request_language(None)


def _user(db: Session, code: str, role: Role = Role.A, active: bool = True) -> int:
    user = User(
        username=code.lower(), code=code, full_name=code, hashed_password="x",
        role=role, status=UserStatus.active if active else UserStatus.disabled,
    )
    db.add(user)
    db.flush()
    return user.id


def _flights(db: Session, pairs: dict[date, int]) -> None:
    db.add_all(FlightDay(day=d, flight_pairs=p) for d, p in pairs.items())
    db.flush()


def _leave(
    db: Session, uid: int, start: date, end: date,
    status: LeaveStatus = LeaveStatus.pending,
) -> LeaveRequest:
    req = LeaveRequest(
        user_id=uid, start_date=start, end_date=end,
        leave_type=LeaveType.monthly, status=status,
    )
    db.add(req)
    db.flush()
    return req


def _roster(
    db: Session, year: int, month: int, cells: dict[tuple[int, date], AttendanceCode]
) -> None:
    schedule = MonthlySchedule(year=year, month=month, status=ScheduleStatus.draft)
    db.add(schedule)
    db.flush()
    db.add_all(
        ShiftAssignment(schedule_id=schedule.id, user_id=u, work_date=d, code=c)
        for (u, d), c in cells.items()
    )
    db.flush()


def _risk(db: Session, req: LeaveRequest) -> list[str]:
    return leave_staffing.warnings_for(leave_staffing.load(db, [req]), req)


# --- month without a schedule: head count ------------------------------------


def test_no_schedule_reports_head_count(db: Session) -> None:
    """3 role-A people; one other on approved leave → 1 left for 1 ARR + 2 DEP."""
    a1, _a2, a3 = (_user(db, c) for c in ("A1", "A2", "A3"))
    _user(db, "T1", Role.T)  # never counted
    _user(db, "A9", active=False)  # disabled: not counted
    d1, d2, d3 = date(2041, 6, 10), date(2041, 6, 11), date(2041, 6, 12)
    _flights(db, {d1: 2, d2: 1, d3: 0})
    _leave(db, a3, d1, d1, LeaveStatus.approved)
    req = _leave(db, a1, d1, d3)

    assert _risk(db, req) == [
        "2041-06-10: 1 group-A staff left, 1 ARR + 2 DEP needed",
        # 06-11: a2 + a3 remain for 1 ARR + 1 DEP → covered; 06-12 no flights
    ]

    set_request_language("vi")
    assert _risk(db, req) == [
        "2041-06-10: còn 1 người nhóm A, cần 1 ca ARR + 2 ca DEP"
    ]


def test_approved_request_counts_the_requester_away_too(db: Session) -> None:
    a1, _a2 = _user(db, "A1"), _user(db, "A2")
    day = date(2041, 7, 3)
    _flights(db, {day: 1})
    req = _leave(db, a1, day, day, LeaveStatus.approved)
    assert _risk(db, req) == ["2041-07-03: 1 group-A staff left, 1 ARR + 1 DEP needed"]


# --- month with a schedule: the roster ----------------------------------------


def test_schedule_reports_short_shifts_only_where_the_leave_matters(db: Session) -> None:
    a1, a2, a3 = (_user(db, c) for c in ("A1", "A2", "A3"))
    d1, d2, d3, d4 = (date(2041, 8, d) for d in (4, 5, 6, 7))
    _flights(db, {d1: 2, d2: 1, d3: 2, d4: 1})
    _roster(db, 2041, 8, {
        # d1: requester AL; others give 1 ARR (A/D) + 1 DEP (A/D) → 1 DEP short
        (a1, d1): AL, (a2, d1): AD, (a3, d1): X,
        # d2: requester was X anyway → skipped although nobody else works
        (a1, d2): X, (a2, d2): X, (a3, d2): CD,
        # d3: requester AL; nobody else on duty → both shifts short
        (a1, d3): AL, (a2, d3): X, (a3, d3): X,
        # d4: requester AL; others cover 1 ARR + 1 DEP → nothing
        (a1, d4): AL, (a2, d4): A, (a3, d4): D,
    })
    req = _leave(db, a1, d1, d4, LeaveStatus.approved)

    assert _risk(db, req) == [
        "2041-08-04: 1 short on the DEP shift",
        "2041-08-06: 1 short on the ARR shift",
        "2041-08-06: 2 short on the DEP shift",
    ]
    set_request_language("vi")
    assert _risk(db, req) == [
        "2041-08-04: thiếu 1 người ca DEP",
        "2041-08-06: thiếu 1 người ca ARR",
        "2041-08-06: thiếu 2 người ca DEP",
    ]


def test_pending_request_reports_the_risk_if_approved(db: Session) -> None:
    """Pending: the requester's working cell would go; an X day is skipped."""
    a1, a2 = _user(db, "A1"), _user(db, "A2")
    d1, d2 = date(2041, 9, 1), date(2041, 9, 2)
    _flights(db, {d1: 1, d2: 1})
    _roster(db, 2041, 9, {(a1, d1): A, (a2, d1): D, (a1, d2): X, (a2, d2): X})
    req = _leave(db, a1, d1, d2)
    assert _risk(db, req) == ["2041-09-01: 1 short on the ARR shift"]


def test_span_across_generated_and_missing_month(db: Session) -> None:
    a1, _a2 = _user(db, "A1"), _user(db, "A2")
    d1, d2 = date(2041, 10, 31), date(2041, 11, 1)
    _flights(db, {d1: 1, d2: 2})
    _roster(db, 2041, 10, {(a1, d1): A})
    req = _leave(db, a1, d1, d2)
    assert _risk(db, req) == [
        "2041-10-31: 1 short on the ARR shift",
        "2041-10-31: 1 short on the DEP shift",
        "2041-11-01: 1 group-A staff left, 1 ARR + 2 DEP needed",
    ]


# --- who gets no lines ----------------------------------------------------------


def test_non_role_a_and_rejected_get_none(db: Session) -> None:
    a1, t1 = _user(db, "A1"), _user(db, "T1", Role.T)
    day = date(2041, 12, 1)
    _flights(db, {day: 2})
    rejected = _leave(db, a1, day, day, LeaveStatus.rejected)
    other_role = _leave(db, t1, day, day)
    ctx = leave_staffing.load(db, [rejected, other_role])
    assert leave_staffing.warnings_for(ctx, rejected) == []
    assert leave_staffing.warnings_for(ctx, other_role) == []


def test_list_loads_in_a_fixed_number_of_queries(db: Session) -> None:
    """No per-row or per-day queries: 5 whatever the list holds."""
    from sqlalchemy import event

    ids = [_user(db, f"A{i}") for i in range(1, 6)]
    _flights(db, {date(2042, 1, d): 2 for d in range(1, 29)})
    _roster(db, 2042, 1, {(u, date(2042, 1, d)): A for u in ids for d in range(1, 29)})
    reqs = [
        _leave(db, u, date(2042, 1, 1 + 5 * i), date(2042, 2, 3 + 5 * i))
        for i, u in enumerate(ids)
    ]
    statements: list[str] = []
    engine = db.get_bind()
    listener = lambda *args: statements.append(args[2])  # noqa: E731
    event.listen(engine, "before_cursor_execute", listener)
    try:
        rows = leave_staffing.with_staffing_warnings(db, reqs)
    finally:
        event.remove(engine, "before_cursor_execute", listener)
    assert len(rows) == 5 and len(statements) == 5, statements
    assert all(r.staffing_warnings for r in rows)


# --- approving returns the same lines the row shows ---------------------------


def test_approve_returns_the_row_lines(db: Session) -> None:
    a1, a2 = _user(db, "A1"), _user(db, "A2")
    d1, d2 = date(2042, 3, 2), date(2042, 3, 3)
    _flights(db, {d1: 1, d2: 2})
    _roster(db, 2042, 3, {(a1, d1): A, (a2, d1): D, (a1, d2): D, (a2, d2): A})
    req = _leave(db, a1, d1, d2)
    db.commit()
    before = _risk(db, req)
    assert before == [
        "2042-03-02: 1 short on the ARR shift",
        "2042-03-03: 2 short on the DEP shift",
    ]

    decided, warnings = leave_service.decide(db, req.id, LeaveStatus.approved, admin_id=1)

    after = _risk(db, decided)
    assert after == before  # the cells became AL: same days still matter
    assert all(line in warnings for line in after)


def test_approve_without_schedule_returns_the_row_lines(db: Session) -> None:
    a1, _a2 = _user(db, "A1"), _user(db, "A2")
    day = date(2042, 4, 7)
    _flights(db, {day: 2})
    req = _leave(db, a1, day, day)
    db.commit()
    _, warnings = leave_service.decide(db, req.id, LeaveStatus.approved, admin_id=1)
    line = "2042-04-07: 1 group-A staff left, 1 ARR + 2 DEP needed"
    assert line in warnings
    assert _risk(db, req) == [line]


# --- the endpoints (shared database, 2047) -------------------------------------


def _bearer(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_admin_lists_carry_the_risk_employee_list_does_not(client: TestClient) -> None:
    admin = _bearer(client, "admin", "admin123")
    res = client.post(
        f"{V}/users", headers=admin,
        json={"username": "staffing_row_a1", "full_name": "Staffing Row",
              "password": "secret1", "role": "A"},
    )
    assert res.status_code == 201, res.text
    uid = res.json()["id"]
    day = date(2047, 5, 14)
    # Hand-made 2047-05 roster with only this person's cell: nobody else is on
    # ARR/DEP that day, whoever else exists in the shared database.
    db = SessionLocal()
    try:
        _flights(db, {day: 1})
        _roster(db, 2047, 5, {(uid, day): A})
        db.commit()
    finally:
        db.close()
    employee = _bearer(client, "staffing_row_a1", "secret1")
    res = client.post(
        f"{V}/leaves", headers=employee,
        json={"start_date": day.isoformat(), "end_date": day.isoformat()},
    )
    assert res.status_code == 201, res.text
    leave_id = res.json()["id"]
    assert res.json()["staffing_warnings"] == []

    expected_en = [
        "2047-05-14: 1 short on the ARR shift",
        "2047-05-14: 1 short on the DEP shift",
    ]
    expected_vi = ["2047-05-14: thiếu 1 người ca ARR", "2047-05-14: thiếu 1 người ca DEP"]

    def row(path: str, headers: dict[str, str], lang: str = "en") -> dict:
        res = client.get(f"{V}{path}", headers={**headers, "Accept-Language": lang})
        assert res.status_code == 200, res.text
        return next(r for r in res.json() if r["id"] == leave_id)

    assert row("/leaves?all=true", admin)["staffing_warnings"] == expected_en
    assert row("/leaves/pending", admin)["staffing_warnings"] == expected_en
    assert row("/leaves?all=true", admin, "vi")["staffing_warnings"] == expected_vi
    assert row("/leaves", employee)["staffing_warnings"] == []

    res = client.post(
        f"{V}/leaves/{leave_id}/decide", headers=admin, json={"status": "approved"}
    )
    assert res.status_code == 200, res.text
    assert all(line in res.json()["warnings"] for line in expected_en)
    assert row("/leaves?all=true", admin)["staffing_warnings"] == expected_en

    res = client.post(f"{V}/leaves/{leave_id}/revoke", headers=admin)
    assert res.status_code == 200, res.text
    assert row("/leaves?all=true", admin)["staffing_warnings"] == []
