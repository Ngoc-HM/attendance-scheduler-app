"""Shift-change requests (locked decision #8, spec §3).

A user asks to change the code of one of their OWN scheduled days
(``change_code``) or to exchange that day's codes with a colleague
(``swap_with``). Admin approves/rejects; approval applies the edit to the
schedule with a hard-rule re-check (phase 05 ``apply_shift_change``).

A swap needs both people (customer 2026-11-18): the requester files it, the
colleague accepts or declines (``counterpart_status``), and only an accepted
swap reaches the admin, who decides last. A declined swap is rejected.

Flexible roles (M, T) request routinely; fixed roles (A1–A4) may request but
the admin reviews strictly (§3) — the ``strict_review`` flag is derived from
the requester's role, not stored.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import AttendanceCode, LeaveStatus, SwapKind


class ShiftChangeRequest(Base, TimestampMixin):
    __tablename__ = "shift_change_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    work_date: Mapped[date] = mapped_column(Date, index=True)

    kind: Mapped[SwapKind] = mapped_column(SAEnum(SwapKind, name="swap_kind"))
    # change_code: the desired new code for the requester's cell.
    requested_code: Mapped[AttendanceCode | None] = mapped_column(
        SAEnum(AttendanceCode, name="attendance_code"), nullable=True
    )
    # swap_with: the colleague whose same-day code is exchanged.
    counterpart_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # swap_with only: the colleague's own answer — pending until they accept
    # (approved) or decline (rejected); NULL for a code change.
    counterpart_status: Mapped[LeaveStatus | None] = mapped_column(
        SAEnum(LeaveStatus, name="leave_status"), nullable=True
    )
    counterpart_decided_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # Reuses the pending/approved/rejected lifecycle from leave requests.
    status: Mapped[LeaveStatus] = mapped_column(
        SAEnum(LeaveStatus, name="leave_status"), default=LeaveStatus.pending
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    decided_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
