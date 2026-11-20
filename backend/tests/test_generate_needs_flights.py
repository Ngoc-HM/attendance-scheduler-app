"""No roster without the month's flights; fill a month from the previous
one by weekday (owner 2026-11-20)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, time

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.core.i18n import set_request_language
from app.models.enums import Role, UserStatus
from app.models.flight import Flight, FlightDay
from app.models.schedule import MonthlySchedule
from app.models.user import User
from app.scheduler.calendar_utils import carry_days, month_days
from app.services import flight_service, schedule_service

NOV, DEC = (2026, 11), (2026, 12)


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch) -> Iterator[Session]:
    monkeypatch.setattr(settings, "GENERATE_REQUIRES_FLIGHTS", True)
    monkeypatch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", 15.0)
    set_request_language("en")
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    session.add(User(username="t1", code="T1", full_name="T1", hashed_password="x",
                     role=Role.T, status=UserStatus.active))
    session.commit()
    try:
        yield session
    finally:
        set_request_language(None)
        session.close()
        engine.dispose()


def _enter(db: Session, days: list[date], pairs: int = 2) -> None:
    db.add_all(FlightDay(day=d, flight_pairs=pairs) for d in days)
    db.commit()


def test_generate_is_refused_until_every_day_has_flights(db: Session) -> None:
    with pytest.raises(HTTPException) as err:
        schedule_service.generate(db, *NOV)
    assert err.value.status_code == 422
    assert "11/2026" in err.value.detail and "30 day(s)" in err.value.detail

    days = month_days(*NOV)
    _enter(db, days[:-2])
    db.add(FlightDay(day=days[-2], flight_pairs=0))  # a row without flights is not entered
    db.commit()
    with pytest.raises(HTTPException) as err:
        schedule_service.generate(db, *NOV)
    assert "2 day(s) (29/11, 30/11)" in err.value.detail
    assert db.query(MonthlySchedule).count() == 0

    db.query(FlightDay).filter(FlightDay.day == days[-2]).update({"flight_pairs": 2})
    _enter(db, days[-1:])
    assert schedule_service.generate(db, *NOV).feasible


def test_generate_tells_the_admin_the_next_month_has_no_flights(db: Session) -> None:
    _enter(db, month_days(*NOV))
    result = schedule_service.generate(db, *NOV)
    assert result.feasible
    assert {a.work_date for a in result.schedule.carry_assignments} == set(carry_days(*NOV))
    assert result.notices == [
        "Flights for 12/2026 are not entered yet (01/12, 02/12, 03/12, 04/12, 05/12, "
        "06/12): these days were planned with the usual flights of their weekday. "
        "Enter the flights of 12/2026."
    ]

    _enter(db, carry_days(*NOV))
    assert schedule_service.generate(db, *NOV, force=True).notices == []


def _leg(day: date, flt: int, hour: int) -> Flight:
    return Flight(day=day, flt_number=flt, route="HAN-FRA", sta=time(hour, 30), std=time(hour, 0))


def test_a_month_is_filled_from_the_previous_months_last_week_by_weekday(db: Session) -> None:
    # Last week of November 2026: Tue 24 … Mon 30. Tuesday has one pair,
    # Wednesday two; Thursday has nothing entered.
    tue, wed = date(2026, 11, 24), date(2026, 11, 25)
    db.add_all([_leg(tue, 37, 6), _leg(tue, 36, 13),
                _leg(wed, 37, 6), _leg(wed, 36, 13), _leg(wed, 31, 5), _leg(wed, 30, 12)])
    # An older Tuesday must not be the reference, and a December day that
    # already has flights is replaced.
    db.add_all([_leg(date(2026, 11, 17), 31, 5), _leg(date(2026, 11, 17), 30, 12),
                _leg(date(2026, 12, 1), 31, 5), _leg(date(2026, 12, 3), 31, 5)])
    db.commit()

    days, skipped = flight_service.apply_previous_month(db, *DEC)

    assert skipped == [0, 3, 4, 5, 6]  # only Tuesday and Wednesday had flights
    by_day = {fd.day: fd.flight_pairs for fd in days}
    legs = flight_service.list_flights_for_days(db, month_days(*DEC))
    for d in month_days(*DEC):
        numbers = sorted(f.flt_number for f in legs[d])
        if d.weekday() == 1:
            assert numbers == [36, 37] and by_day[d] == 1, d
        elif d.weekday() == 2:
            assert numbers == [30, 31, 36, 37] and by_day[d] == 2, d
        elif d == date(2026, 12, 3):
            assert numbers == [31]  # Thursday: no reference, left as it was
        else:
            assert numbers == [], d
    first_tuesday = legs[date(2026, 12, 1)]
    assert {(f.flt_number, f.sta, f.std) for f in first_tuesday} == {
        (37, time(6, 30), time(6, 0)), (36, time(13, 30), time(13, 0)),
    }


def test_filling_from_an_empty_previous_month_is_refused(db: Session) -> None:
    with pytest.raises(HTTPException) as err:
        flight_service.apply_previous_month(db, *DEC)
    assert err.value.status_code == 409
    assert err.value.detail == "The last week of the previous month has no flights to copy."


# --- delete a month's roster (owner 2026-11-20) ------------------------------


def _months(db: Session) -> dict[tuple[int, int], int]:
    return {
        (s.year, s.month): len(s.assignments)
        for s in db.query(MonthlySchedule).order_by(MonthlySchedule.year, MonthlySchedule.month)
    }


def test_deleting_a_month_removes_it_and_the_days_it_ran_into(db: Session) -> None:
    from app.models.attendance import AttendanceRecord
    from app.models.enums import AttendanceCode
    from app.models.schedule import ShiftAssignment

    _enter(db, month_days(*NOV) + month_days(*DEC))
    assert schedule_service.generate(db, *NOV).feasible
    assert _months(db) == {NOV: 30, DEC: 6}  # one person; 1–6 Dec carried

    # A seeded actual goes with the roster, a recorded one stays.
    uid = db.query(ShiftAssignment.user_id).first()[0]
    db.add_all([
        AttendanceRecord(user_id=uid, work_date=date(2026, 11, 3), code=AttendanceCode.AD),
        AttendanceRecord(user_id=uid, work_date=date(2026, 11, 4), code=AttendanceCode.AD,
                         recorded_by=uid),
    ])
    db.commit()

    schedule_service.delete_month(db, *NOV)

    assert _months(db) == {}  # December held only November's carried days
    assert [r.work_date for r in db.query(AttendanceRecord)] == [date(2026, 11, 4)]
    with pytest.raises(HTTPException) as err:
        schedule_service.delete_month(db, *NOV)
    assert err.value.status_code == 404


def test_deleting_a_month_leaves_a_generated_next_month_whole(db: Session) -> None:
    from app.models.schedule import ShiftAssignment

    _enter(db, month_days(*NOV) + month_days(*DEC) + month_days(2027, 1))
    assert schedule_service.generate(db, *NOV).feasible
    assert schedule_service.generate(db, *DEC).feasible
    assert _months(db) == {NOV: 30, DEC: 31, (2027, 1): 3}

    schedule_service.delete_month(db, *NOV)

    # December keeps all its days; 1–6 Dec are its own cells now.
    assert _months(db) == {DEC: 31, (2027, 1): 3}
    december = (
        db.query(ShiftAssignment)
        .join(MonthlySchedule, ShiftAssignment.schedule_id == MonthlySchedule.id)
        .filter(MonthlySchedule.year == 2026, MonthlySchedule.month == 12)
    )
    assert not any(a.carried for a in december)

    # Deleting December also takes the days it ran into January.
    schedule_service.delete_month(db, *DEC)
    assert _months(db) == {}


def test_delete_endpoint_is_admin_only(client) -> None:
    v = "/api/v1"
    assert client.delete(f"{v}/schedules/2051/3").status_code == 401
    token = client.post(
        f"{v}/auth/login", data={"username": "admin", "password": "admin123"}
    ).json()["access_token"]
    admin = {"Authorization": f"Bearer {token}"}
    assert client.delete(f"{v}/schedules/2051/3", headers=admin).status_code == 404
