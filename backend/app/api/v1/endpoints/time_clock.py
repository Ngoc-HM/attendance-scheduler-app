"""Time-clock endpoints — real check-in / check-out (owner request 2026-07-09).

All routes are own-data only (user id from token). Registered under
``/attendance/clock`` — distinct sub-path, no clash with the attendance grid.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import ActiveUser, DbSession
from app.schemas.time_clock import TimeClockRead
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


@router.get("/today", response_model=TimeClockRead | None)
def clock_today(db: DbSession, current_user: ActiveUser):
    """Today's own entry — None when not clocked in yet."""
    return time_clock_service.get_today(db, current_user.id)


@router.get("/me", response_model=list[TimeClockRead])
def clock_month_me(db: DbSession, year: int, month: int, current_user: ActiveUser):
    """Own check-in/out history for the given month."""
    return time_clock_service.list_month_for_user(db, current_user.id, year, month)
