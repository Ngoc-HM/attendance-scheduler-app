"""Admin dashboard and the leave report (customer 2026-11-18)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.business_time import business_today
from app.core.database import Base
from app.models.enums import (
    AttendanceCode,
    LeaveStatus,
    LeaveType,
    Role,
    ScheduleStatus,
    UserStatus,
)
from app.models.leave import LeaveRequest
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.services import dashboard_service, report_service

V = "/api/v1"


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


def _user(db: Session, code: str, role: Role, quota: int = 30) -> int:
    user = User(
        username=code.lower(), code=code, full_name=code, hashed_password="x",
        role=role, status=UserStatus.active, annual_leave_quota=quota,
    )
    db.add(user)
    db.flush()
    return user.id


def test_overview_reads_today_missing_punches_roster_and_leave(db: Session) -> None:
    today = business_today()
    admin = _user(db, "M1", Role.M)
    a1, f1 = _user(db, "A1", Role.A), _user(db, "F1", Role.F, quota=20)
    schedule = MonthlySchedule(
        year=today.year, month=today.month, status=ScheduleStatus.published
    )
    db.add(schedule)
    db.flush()
    cells = {(admin, today): AttendanceCode.O_D, (a1, today): AttendanceCode.A,
             (f1, today): AttendanceCode.X}
    yesterday = today - timedelta(days=1)
    if yesterday.month == today.month:
        cells[(a1, yesterday)] = AttendanceCode.D  # worked, never punched
    db.add_all(
        ShiftAssignment(schedule_id=schedule.id, user_id=u, work_date=d, code=c)
        for (u, d), c in cells.items()
    )
    db.add_all([
        LeaveRequest(user_id=f1, start_date=date(today.year, 3, 2),
                     end_date=date(today.year, 3, 4), leave_type=LeaveType.monthly,
                     status=LeaveStatus.approved),
        LeaveRequest(user_id=f1, start_date=date(today.year, 8, 3),
                     end_date=date(today.year, 8, 4), leave_type=LeaveType.monthly,
                     status=LeaveStatus.pending),
    ])
    db.commit()

    view = dashboard_service.overview(db)

    assert view.today == today
    assert [(d.code, d.shift) for d in view.working] == [("A1", AttendanceCode.A)]
    assert [(d.code, d.shift) for d in view.off] == [("F1", AttendanceCode.X)]
    if yesterday.month == today.month:
        assert [(m.code, m.work_date, m.status) for m in view.missing_clock] == [
            ("A1", yesterday, "absent")
        ]
    assert view.pending.leaves == 1
    assert view.this_month.status is ScheduleStatus.published
    assert view.next_month.status is None and view.next_month.violations == []
    leave = {row.code: row for row in view.leave}
    assert set(leave) == {"A1", "F1"}  # the admin account is left out
    assert (leave["F1"].quota, leave["F1"].used, leave["F1"].pending,
            leave["F1"].available) == (20, 3, 2, 15)


def test_leave_report_lists_every_active_person(db: Session) -> None:
    a1 = _user(db, "A1", Role.A, quota=10)
    db.add(LeaveRequest(user_id=a1, start_date=date(2044, 5, 2),
                        end_date=date(2044, 5, 3), leave_type=LeaveType.monthly,
                        status=LeaveStatus.approved))
    db.commit()

    table = report_service.leave_balance_report(db, 2044)

    assert table.headers == [
        "Code", "User", "Role", "Quota", "Approved", "Pending", "Left", "Comp days",
    ]
    assert table.rows == [["A1", "A1", "A", "10", "2", "0", "8", "0"]]


def test_dashboard_and_leave_report_are_admin_only(client: TestClient) -> None:
    token = client.post(
        f"{V}/auth/login", data={"username": "admin", "password": "admin123"}
    ).json()["access_token"]
    admin = {"Authorization": f"Bearer {token}"}
    ok = client.get(f"{V}/dashboard", headers=admin)
    assert ok.status_code == 200
    assert {"today", "working", "off", "missing_clock", "pending", "this_month",
            "next_month", "leave_year", "leave"} <= set(ok.json())
    report = client.get(f"{V}/reports/leave-balance/2044?format=xlsx", headers=admin)
    assert report.status_code == 200
    assert client.get(f"{V}/dashboard").status_code == 401
