"""Aggregates all v1 endpoint routers under ``/api/v1``."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    attendance,
    auth,
    calculations,
    flights,
    holidays,
    leaves,
    reports,
    schedules,
    self_arrange,
    shift_changes,
    time_clock,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(flights.router, prefix="/flights", tags=["flights"])
api_router.include_router(leaves.router, prefix="/leaves", tags=["leaves"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
# Registered before nothing conflicting: /attendance/clock/* is a distinct sub-path.
api_router.include_router(
    time_clock.router, prefix="/attendance/clock", tags=["time-clock"]
)
api_router.include_router(holidays.router, prefix="/holidays", tags=["holidays"])
api_router.include_router(
    calculations.router, prefix="/calculations", tags=["calculations"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(shift_changes.router, prefix="/shift-changes", tags=["shift-changes"])
api_router.include_router(self_arrange.router, prefix="/self-arrange", tags=["self-arrange"])
