"""Time-clock DTOs (check-in / check-out, owner request 2026-07-09)."""

from __future__ import annotations

from datetime import date, datetime

from app.schemas.common import ORMModel


class TimeClockRead(ORMModel):
    id: int
    user_id: int
    work_date: date
    check_in_at: datetime | None
    check_out_at: datetime | None
