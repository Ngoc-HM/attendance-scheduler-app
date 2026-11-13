"""Real check-in / check-out timestamps (owner request 2026-07-09).

Deliberately decoupled from ``AttendanceRecord`` (the admin code grid): the
time clock stores WHEN a person clocked in/out, never derives or alters the
per-day attendance code (owner decision e). One row per (user, day).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class TimeClockEntry(Base, TimestampMixin):
    __tablename__ = "time_clock_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "work_date", name="uq_time_clock_cell"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    work_date: Mapped[date] = mapped_column(Date, index=True)
    check_in_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    check_out_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Admin who last set this day by hand (PUT /attendance/clock/staff);
    # NULL = the person punched it themself.
    corrected_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", name="fk_time_clock_corrected_by", ondelete="SET NULL"),
        nullable=True,
    )
