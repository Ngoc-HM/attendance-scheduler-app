"""Working-time frame of each shift (owner 2026-11-18, decision #71).

One row per editable shift code (``A``, ``D``). The double shift's frame
(``A/D``, ``AD``) is never stored: it is derived from these two rows as the
earliest start to the latest end, so it can never disagree with its parts.
Display only: no check-in/out rule reads these times.
"""

from __future__ import annotations

from datetime import time

from sqlalchemy import String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class ShiftTime(Base, TimestampMixin):
    __tablename__ = "shift_times"
    __table_args__ = (UniqueConstraint("code", name="uq_shift_times_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # "A" or "D" (AttendanceCode values of the two single shifts).
    code: Mapped[str] = mapped_column(String(4))
    # Wall-clock times in the business zone (Frankfurt), start before end.
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
