"""Self-arrange batch request schemas (owner 2026-07-09)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import AttendanceCode, LeaveStatus
from app.schemas.common import ORMModel

# 2 changes per day is impossible; 62 caps a full month of paired swaps.
MAX_CHANGES = 62


class SelfArrangeChange(BaseModel):
    work_date: date
    code: AttendanceCode


class SelfArrangeCreate(BaseModel):
    """Payload for POST /self-arrange — the requester's own cells only."""

    year: int
    month: int = Field(ge=1, le=12)
    changes: list[SelfArrangeChange] = Field(min_length=1, max_length=MAX_CHANGES)
    # SelfArrangeRequest.note is String(255).
    note: str | None = Field(default=None, max_length=255)


class SelfArrangeDecision(BaseModel):
    """Admin approve/reject payload."""

    status: LeaveStatus  # approved | rejected only


class SelfArrangeRead(ORMModel):
    id: int
    requester_id: int
    year: int
    month: int
    changes: list[SelfArrangeChange]
    status: LeaveStatus
    note: str | None
    decided_by_id: int | None
    decided_at: datetime | None
    created_at: datetime
    # Recheck warnings surfaced to the admin after an approval is applied.
    warnings: list[str] = []
