"""Time-clock DTOs (check-in / check-out, owner request 2026-07-09)."""

from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel

from app.schemas.common import ORMModel


class TimeClockRead(ORMModel):
    id: int
    user_id: int
    work_date: date
    check_in_at: datetime | None
    check_out_at: datetime | None


class TimeClockStaffRead(TimeClockRead):
    """An entry in the admin's month list: who it belongs to."""

    full_name: str
    code: str
    # The punches as HH:MM in the business TIMEZONE (Frankfurt): what the
    # admin reads and corrects, whatever the device's own zone is.
    check_in_local: str | None = None
    check_out_local: str | None = None


class TimeClockCorrect(BaseModel):
    """Admin correction of one person's day (a forgotten or wrong punch).

    Times are local times of the business ``TIMEZONE`` on ``work_date``;
    ``check_out`` left out keeps the day open (still at work).
    """

    user_id: int
    work_date: date
    check_in: time
    check_out: time | None = None
