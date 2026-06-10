"""Generated monthly schedule (spec §4.4 / F-07..F-10).

``MonthlySchedule`` is one solver run for a (year, month). ``ShiftAssignment``
holds the per-(person, day) result, including any admin manual override
(F-09) flagged for the audit trail.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Boolean
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import AttendanceCode, ScheduleStatus


class MonthlySchedule(Base, TimestampMixin):
    __tablename__ = "monthly_schedules"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_schedule_year_month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    status: Mapped[ScheduleStatus] = mapped_column(
        SAEnum(ScheduleStatus, name="schedule_status"), default=ScheduleStatus.draft
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    assignments: Mapped[list["ShiftAssignment"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan"
    )


class ShiftAssignment(Base, TimestampMixin):
    __tablename__ = "shift_assignments"
    __table_args__ = (
        UniqueConstraint(
            "schedule_id", "user_id", "work_date", name="uq_assignment_cell"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    schedule_id: Mapped[int] = mapped_column(
        ForeignKey("monthly_schedules.id"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    work_date: Mapped[date] = mapped_column(Date, index=True)
    code: Mapped[AttendanceCode] = mapped_column(
        SAEnum(AttendanceCode, name="attendance_code")
    )
    # True when an admin edited this cell after auto-generation (F-09).
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False)

    schedule: Mapped["MonthlySchedule"] = relationship(back_populates="assignments")
