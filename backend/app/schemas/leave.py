"""Leave request schemas (F-05, F-06)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.models.enums import LeaveStatus, LeaveType
from app.schemas.common import ORMModel


class LeaveCreate(BaseModel):
    start_date: date
    end_date: date
    # leave_type is accepted from caller but overridden by auto-classification
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
