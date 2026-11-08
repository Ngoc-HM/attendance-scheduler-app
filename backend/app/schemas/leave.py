"""Leave request schemas (F-05, F-06)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.models.enums import LeaveStatus, LeaveType
from app.schemas.common import ORMModel


class LeaveCreate(BaseModel):
    start_date: date
    end_date: date
    # leave_type is optional (two distinct UI flows); the service always
    # classifies by span and rejects a supplied leave_type that disagrees.
    leave_type: LeaveType | None = None
    note: str | None = None


class LeaveDecision(BaseModel):
    """Admin approve/reject (spec §3, §5.4 #9)."""

    status: LeaveStatus


class LeaveRead(ORMModel):
    id: int
    user_id: int
    start_date: date
    end_date: date
    leave_type: LeaveType
    status: LeaveStatus
    note: str | None
    # Decision-time notices (e.g. an already-generated month is now stale).
    warnings: list[str] = []


class ConflictEntry(ORMModel):
    """Single ranked entry returned by GET /leaves/conflicts."""

    id: int
    user_id: int
    start_date: date
    end_date: date
    leave_type: LeaveType
    status: LeaveStatus
    note: str | None
    # Rank position (1 = highest priority).
    rank: int


class LeaveWindowRead(BaseModel):
    """Registration window state for the client (GET /leaves/window).

    ``monthly_open`` says whether leave for ``monthly_target_month`` can be
    filed today (days 1–``closes_on_day`` of the month before it); annual
    leave can be filed for ``annual_target_year``. When ``enforced`` is false
    (dev) the window never closes.
    """

    monthly_open: bool
    monthly_target_year: int
    monthly_target_month: int
    annual_target_year: int
    closes_on_day: int
    enforced: bool


class AnnualLeaveSummary(BaseModel):
    """One person's leave for a calendar year (GET /leaves/balance, D4).

    ``used`` / ``pending`` are the approved / pending leave days that fall
    inside ``year``; ``remaining = quota - used`` (negative once an admin
    approved past the quota).
    """

    year: int
    quota: int
    used: int
    pending: int
    remaining: int
