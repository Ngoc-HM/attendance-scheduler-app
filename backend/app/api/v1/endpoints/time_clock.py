"""Time-clock endpoints — real check-in / check-out (owner request 2026-07-09).

All routes are own-data only (user id from token). Registered under
``/attendance/clock`` — distinct sub-path, no clash with the attendance grid.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.api.params import MonthQuery, YearQuery
from app.schemas.time_clock import (
    ClockNow,
    TimeClockBoardCell,
    TimeClockCorrect,
    TimeClockRead,
    TimeClockStaffRead,
)
from app.services import audit_service, time_clock_service

router = APIRouter()


@router.post("/check-in", response_model=TimeClockRead, status_code=status.HTTP_201_CREATED)
def clock_check_in(db: DbSession, current_user: ActiveUser):
    """Record the current user's check-in for today (409 if already done)."""
    entry = time_clock_service.check_in(db, current_user.id)
    audit_service.record(db, current_user.id, "clock.check_in", "TimeClockEntry", entry.id)
    return entry


@router.post("/check-out", response_model=TimeClockRead)
def clock_check_out(db: DbSession, current_user: ActiveUser):
    """Record the current user's check-out for today (requires check-in)."""
    entry = time_clock_service.check_out(db, current_user.id)
    audit_service.record(db, current_user.id, "clock.check_out", "TimeClockEntry", entry.id)
    return entry


@router.get("/now", response_model=ClockNow)
def clock_now(_user: ActiveUser):
    """The business clock (Frankfurt) right now. The app asks this instead of
    trusting its device clock; punches are always stamped by the server."""
    return time_clock_service.now_local()


@router.get("/today", response_model=TimeClockRead | None)
def clock_today(db: DbSession, current_user: ActiveUser):
    """Today's own entry — None when not clocked in yet."""
    return time_clock_service.get_today(db, current_user.id)


@router.get("/me", response_model=list[TimeClockRead])
def clock_month_me(db: DbSession, year: YearQuery, month: MonthQuery, current_user: ActiveUser):
    """Own check-in/out history for the given month."""
    return time_clock_service.list_month_for_user(db, current_user.id, year, month)


@router.get("/staff", response_model=list[TimeClockStaffRead])
def clock_month_staff(db: DbSession, year: YearQuery, month: MonthQuery, _admin: AdminUser):
    """Admin: everyone's check-in/out of the month (who was in, who forgot to
    check out)."""
    return [
        TimeClockStaffRead(
            **TimeClockRead.model_validate(entry).model_dump(
                exclude={"check_in_local", "check_out_local"}
            ),
            full_name=user.full_name,
            code=user.code,
            corrected=entry.corrected_by is not None,
        )
        for entry, user in time_clock_service.list_month_all(db, year, month)
    ]


@router.put("/staff", response_model=TimeClockRead)
def clock_correct(db: DbSession, payload: TimeClockCorrect, admin: AdminUser):
    """Admin: set a person's check-in/out for a day (a forgotten check-out,
    a missed check-in, a wrong time). Audited."""
    entry = time_clock_service.correct(
        db, payload.user_id, payload.work_date, payload.check_in, payload.check_out,
        corrected_by=admin.id,
    )
    audit_service.record(
        db, admin.id, "clock.correct", "TimeClockEntry", entry.id,
        detail=f"user={payload.user_id} {payload.work_date} "
        f"{payload.check_in}-{payload.check_out or 'open'}",
    )
    return entry


@router.get("/board", response_model=list[TimeClockBoardCell])
def clock_board(db: DbSession, year: YearQuery, month: MonthQuery, _admin: AdminUser):
    """Admin: the month's punches read against the attendance codes — who is
    at work, who forgot to check out, who was due and never checked in."""
    return time_clock_service.board(db, year, month)
