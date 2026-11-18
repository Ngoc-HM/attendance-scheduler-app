"""Warn BEFORE approving (customer 2026-11-18).

``preview_approval`` of a leave or a shift change applies the decision
inside the transaction, collects what it would newly break and rolls back:
the request stays pending and the roster untouched.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.i18n import set_request_language
from app.models.enums import (
    AttendanceCode,
    LeaveStatus,
    LeaveType,
    Role,
    ScheduleStatus,
    SwapKind,
    UserStatus,
)
from app.models.flight import FlightDay
from app.models.leave import LeaveRequest
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.shift_change_request import ShiftChangeRequest
from app.models.user import User
from app.services import leave_service, shift_change_service

A, D, X = AttendanceCode.A, AttendanceCode.D, AttendanceCode.X


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


def _user(db: Session, code: str, quota: int = 30) -> int:
    user = User(
        username=code.lower(), code=code, full_name=code, hashed_password="x",
        role=Role.A, status=UserStatus.active, annual_leave_quota=quota,
    )
    db.add(user)
    db.flush()
    return user.id


def _roster(db: Session, cells: dict[tuple[int, date], AttendanceCode]) -> None:
    schedule = MonthlySchedule(year=2043, month=3, status=ScheduleStatus.draft)
    db.add(schedule)
    db.flush()
    db.add_all(
        ShiftAssignment(schedule_id=schedule.id, user_id=u, work_date=d, code=c)
        for (u, d), c in cells.items()
    )
    db.flush()


def _codes(db: Session) -> dict[tuple[int, date], AttendanceCode]:
    return {(c.user_id, c.work_date): c.code for c in db.query(ShiftAssignment)}


def test_leave_preview_lists_the_short_shift_and_saves_nothing(db: Session) -> None:
    a1, a2 = _user(db, "A1"), _user(db, "A2")
    day = date(2043, 3, 2)
    db.add(FlightDay(day=day, flight_pairs=1))
    cells = {(a1, day): A, (a2, day): D}
    _roster(db, cells)
    req = LeaveRequest(
        user_id=a1, start_date=day, end_date=day,
        leave_type=LeaveType.monthly, status=LeaveStatus.pending,
    )
    db.add(req)
    db.commit()

    lines = leave_service.preview_approval(db, req.id)

    assert lines == ["2043-03-02: 1 short on the A shift"]
    assert db.get(LeaveRequest, req.id).status is LeaveStatus.pending
    assert _codes(db) == cells


def test_leave_preview_is_empty_when_nothing_breaks(db: Session) -> None:
    a1 = _user(db, "A1")
    req = LeaveRequest(
        user_id=a1, start_date=date(2043, 5, 4), end_date=date(2043, 5, 5),
        leave_type=LeaveType.monthly, status=LeaveStatus.pending,
    )
    db.add(req)
    db.commit()
    assert leave_service.preview_approval(db, req.id) == []


def test_leave_preview_reports_the_quota(db: Session) -> None:
    a1 = _user(db, "A1", quota=1)
    req = LeaveRequest(
        user_id=a1, start_date=date(2043, 5, 4), end_date=date(2043, 5, 5),
        leave_type=LeaveType.monthly, status=LeaveStatus.pending,
    )
    db.add(req)
    db.commit()
    assert leave_service.preview_approval(db, req.id) == [
        "Approving exceeds this person's annual leave quota."
    ]


def test_leave_preview_of_a_decided_request_is_refused(db: Session) -> None:
    a1 = _user(db, "A1")
    req = LeaveRequest(
        user_id=a1, start_date=date(2043, 5, 4), end_date=date(2043, 5, 4),
        leave_type=LeaveType.monthly, status=LeaveStatus.approved,
    )
    db.add(req)
    db.commit()
    with pytest.raises(HTTPException) as err:
        leave_service.preview_approval(db, req.id)
    assert err.value.status_code == 409


def test_shift_change_preview_lists_only_what_the_change_adds(db: Session) -> None:
    a1, a2 = _user(db, "A1"), _user(db, "A2")
    d1, d2 = date(2043, 3, 2), date(2043, 3, 3)
    db.add_all([FlightDay(day=d1, flight_pairs=1), FlightDay(day=d2, flight_pairs=1)])
    # d2 is already one short on D: that breach is not this request's doing.
    cells = {(a1, d1): A, (a2, d1): D, (a1, d2): A, (a2, d2): X}
    _roster(db, cells)
    req = ShiftChangeRequest(
        requester_id=a1, work_date=d1, kind=SwapKind.change_code,
        requested_code=X, status=LeaveStatus.pending,
    )
    db.add(req)
    db.commit()

    lines = shift_change_service.preview_approval(db, req.id)

    assert any(line.startswith("2043-03-02") for line in lines)
    assert not any(line.startswith("2043-03-03") for line in lines)
    assert db.get(ShiftChangeRequest, req.id).status is LeaveStatus.pending
    assert _codes(db) == cells


# --- registration ceiling and own cancel (customer 2026-11-18) ---------------


def _file(db: Session, uid: int, start: date, end: date) -> LeaveRequest:
    from app.schemas.leave import LeaveCreate

    return leave_service.create_request(
        db, uid, LeaveCreate(start_date=start, end_date=end), enforce_window=False
    )


def test_a_filed_request_counts_against_the_quota_at_once(db: Session) -> None:
    a1 = _user(db, "A1", quota=5)
    db.commit()
    _file(db, a1, date(2043, 6, 1), date(2043, 6, 3))  # 3 pending

    with pytest.raises(HTTPException) as err:
        _file(db, a1, date(2043, 7, 1), date(2043, 7, 3))  # 3 more > 5
    assert err.value.status_code == 400
    assert err.value.detail == (
        "2043: 2 leave day(s) left to register, this request needs 3."
    )
    _file(db, a1, date(2043, 7, 1), date(2043, 7, 2))  # exactly the 2 left


def test_days_come_back_when_rejected_or_cancelled(db: Session) -> None:
    a1 = _user(db, "A1", quota=3)
    other = _user(db, "A2")
    db.commit()
    first = _file(db, a1, date(2043, 6, 1), date(2043, 6, 3))
    leave_service.decide(db, first.id, LeaveStatus.rejected, admin_id=1)
    second = _file(db, a1, date(2043, 6, 10), date(2043, 6, 12))

    with pytest.raises(HTTPException) as err:  # not the owner
        leave_service.cancel(db, second.id, other)
    assert err.value.status_code == 404
    leave_service.cancel(db, second.id, a1)
    assert db.get(LeaveRequest, second.id) is None
    _file(db, a1, date(2043, 6, 20), date(2043, 6, 22))


def test_only_a_pending_request_can_be_cancelled(db: Session) -> None:
    a1 = _user(db, "A1")
    db.commit()
    req = _file(db, a1, date(2043, 6, 1), date(2043, 6, 2))
    leave_service.decide(db, req.id, LeaveStatus.approved, admin_id=1)
    with pytest.raises(HTTPException) as err:
        leave_service.cancel(db, req.id, a1)
    assert err.value.status_code == 409


def test_the_ceiling_is_judged_per_calendar_year(db: Session) -> None:
    a1 = _user(db, "A1", quota=2)
    db.commit()
    # 2 days in 2043 + 2 days in 2044: each year within its own quota.
    _file(db, a1, date(2043, 12, 30), date(2044, 1, 2))
    with pytest.raises(HTTPException):
        _file(db, a1, date(2044, 3, 1), date(2044, 3, 1))
