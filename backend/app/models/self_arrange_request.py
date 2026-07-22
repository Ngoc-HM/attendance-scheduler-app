"""Self-arrange requests (owner 2026-07-09).

After a schedule is published, flexible roles (T, F — and technically M)
propose a BATCH rearrangement of their OWN cells: a list of
``{"work_date": iso, "code": value}`` changes stored as JSON. A single cell
change always breaks the weekly-2-off quota, so only a set of changes can be
valid — hence the batch shape instead of one row per cell.

Admin approves once more (owner decision b); approval applies every cell to
the published schedule. Reuses the pending/approved/rejected lifecycle.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import LeaveStatus


class SelfArrangeRequest(Base, TimestampMixin):
    __tablename__ = "self_arrange_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)

    # [{"work_date": "2026-07-05", "code": "AD"}, ...] — own cells only.
    changes: Mapped[list] = mapped_column(JSON)

    status: Mapped[LeaveStatus] = mapped_column(
        SAEnum(LeaveStatus, name="leave_status"), default=LeaveStatus.pending
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    decided_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
