"""Leave requests (spec §4.3 / F-05, F-06).

NOTE (GDPR §9.1): sickness (code ``S``) is special-category health data and is
recorded via ``AttendanceRecord`` by an admin, not as a self-service leave
request. Do not store detailed medical reasons here.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import LeaveStatus, LeaveType


class LeaveRequest(Base, TimestampMixin):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    leave_type: Mapped[LeaveType] = mapped_column(SAEnum(LeaveType, name="leave_type"))
    status: Mapped[LeaveStatus] = mapped_column(
        SAEnum(LeaveStatus, name="leave_status"), default=LeaveStatus.pending
    )
    # Optional short note. Never store medical detail for sick leave (§9.1).
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
