"""Shift-change request schemas (locked decision #8, spec §3)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

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
    # ShiftChangeRequest.note is String(255).
    note: str | None = Field(default=None, max_length=255)


class ShiftChangeResponse(BaseModel):
    """The colleague's answer to a swap they were asked into."""

    accept: bool


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
    # When the request was filed: the admin's inbox merges leave, shift
    # changes and sign-ups newest first (owner 2026-11-20).
    created_at: datetime | None = None
    # swap_with: the colleague's own answer (pending / approved / rejected);
    # the admin decides only once it is approved. None for a code change.
    counterpart_status: LeaveStatus | None = None
    # The two people's current roster codes on work_date, read at request
    # time (None without a cell; counterpart_shift None for a code change).
    requester_shift: AttendanceCode | None = None
    counterpart_shift: AttendanceCode | None = None
    # Derived at read time from requester.role.is_fixed (not stored in DB).
    strict_review: bool
    # Non-empty when an approved request's schedule application is pending.
    warnings: list[str] = []
