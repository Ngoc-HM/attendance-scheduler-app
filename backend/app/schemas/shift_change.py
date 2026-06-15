"""Shift-change request schemas (locked decision #8, spec §3)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import AttendanceCode, LeaveStatus, SwapKind
from app.schemas.common import ORMModel


class ShiftChangeCreate(BaseModel):
    """Payload for POST /shift-changes (requester's own cell only)."""

    work_date: date
    kind: SwapKind
    # Required when kind == change_code.
    requested_code: AttendanceCode | None = None
    # Required when kind == swap_with.
    counterpart_user_id: int | None = None
    note: str | None = None


class ShiftChangeDecision(BaseModel):
    """Admin approve/reject payload."""

    status: LeaveStatus  # approved | rejected only


class ShiftChangeRead(ORMModel):
    id: int
    requester_id: int
    work_date: date
    kind: SwapKind
    requested_code: AttendanceCode | None
    counterpart_user_id: int | None
    status: LeaveStatus
    note: str | None
    decided_by_id: int | None
    decided_at: datetime | None
    # Derived at read time from requester.role.is_fixed (not stored in DB).
    strict_review: bool
    # Non-empty when an approved request's schedule application is pending.
    warnings: list[str] = []
