"""Time-clock DTOs (check-in / check-out, owner request 2026-07-09)."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, computed_field

from app.core.business_time import local_hm
from app.schemas.common import ORMModel


class TimeClockRead(ORMModel):
    id: int
    user_id: int
    work_date: date
    check_in_at: datetime | None
    check_out_at: datetime | None

    # The punches as HH:MM on the business clock (Frankfurt): what people
    # read, whatever the zone of their device.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def check_in_local(self) -> str | None:
        return local_hm(self.check_in_at)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def check_out_local(self) -> str | None:
        return local_hm(self.check_out_at)


class ClockNow(BaseModel):
    """The business clock right now (``GET /attendance/clock/now``)."""

    date: date
    time: str
    timezone: str


class TimeClockStaffRead(TimeClockRead):
    """An entry in the admin's month list: who it belongs to."""

    full_name: str
    code: str
    # Set by the admin (PUT /attendance/clock/staff) rather than punched.
    corrected: bool = False


class TimeClockCorrect(BaseModel):
    """Admin correction of one person's day (a forgotten or wrong punch).

    Times are local times of the business ``TIMEZONE`` on ``work_date``;
    ``check_out`` left out keeps the day open (still at work).
    """

    user_id: int
    work_date: date
    check_in: time
    check_out: time | None = None


class TimeClockBoardCell(BaseModel):
    """One (person, day) of the admin's attendance board (see
    ``time_clock_service.board``)."""

    user_id: int
    work_date: date
    check_in_local: str | None
    check_out_local: str | None
    corrected: bool
    # None: an adjusted day nobody punched and nobody was due on.
    status: Literal["working", "missed_out", "absent", "off_day", "ok"] | None
    tint: Literal["missing", "adjusted"] | None = None
