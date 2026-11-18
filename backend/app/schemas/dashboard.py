"""Admin dashboard (customer 2026-11-18): the state of the station at a glance."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

from app.models.enums import AttendanceCode, Role, ScheduleStatus
from app.schemas.pending_counts import PendingCounts


class DashboardPerson(BaseModel):
    user_id: int
    # The person's code (A3, F1, ...); the username when none is assigned.
    code: str
    role: Role


class DashboardDuty(DashboardPerson):
    """One person's roster cell of today, with today's punches."""

    shift: AttendanceCode
    check_in_local: str | None = None
    check_out_local: str | None = None


class DashboardMissing(DashboardPerson):
    """A past working day of this month without check-in or check-out."""

    work_date: date
    status: Literal["absent", "missed_out"]


class DashboardSchedule(BaseModel):
    year: int
    month: int
    # None: the month has no schedule yet.
    status: ScheduleStatus | None
    # Rule breaches of the stored roster, as text.
    violations: list[str] = []


class DashboardLeave(DashboardPerson):
    """One person's annual leave: the ceiling (``quota``) minus what is
    registered — approved or still pending — for ``leave_year`` and for the
    year after, which is the one being registered now."""

    quota: int
    used: int
    pending: int
    # What the person can still register: quota - used - pending.
    available: int
    next_used: int
    next_pending: int
    next_available: int
    carry_comp: int


class DashboardRead(BaseModel):
    today: date
    working: list[DashboardDuty]
    off: list[DashboardDuty]
    missing_clock: list[DashboardMissing]
    pending: PendingCounts
    this_month: DashboardSchedule
    next_month: DashboardSchedule
    leave_year: int
    leave: list[DashboardLeave]
