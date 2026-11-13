"""Actual attendance records (spec §4.5 / F-11, F-12).

Distinct from the *planned* ``ShiftAssignment``: this captures what actually
happened each day (incl. sick ``S``, holidays ``X``, etc.) and is the basis for
day-count and reporting (F-14, F-15). Admin updates leave/sick statuses (F-12).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint, false
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import AttendanceCode


class AttendanceRecord(Base, TimestampMixin):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("user_id", "work_date", name="uq_attendance_cell"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    work_date: Mapped[date] = mapped_column(Date, index=True)
    code: Mapped[AttendanceCode] = mapped_column(
        SAEnum(AttendanceCode, name="attendance_code")
    )
    # Admin who recorded/last-updated this entry (F-12) — for the audit trail.
    recorded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # F-10 sick cover: on the colleague's A/D, the sick (S) actual it covers
    # and what this cell held before, so taking the S back restores it.
    # Any later edit of this cell drops the link (the admin owns it then).
    cover_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("attendance_records.id", name="fk_attendance_cover_of",
                   ondelete="SET NULL"),
        nullable=True, index=True,
    )
    cover_prev_code: Mapped[AttendanceCode | None] = mapped_column(
        SAEnum(AttendanceCode, name="attendance_code"), nullable=True
    )
    # True when the previous cell was still the plan's copy (recorded_by
    # NULL), so the restored cell follows the plan again.
    cover_prev_seeded: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
