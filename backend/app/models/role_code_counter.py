"""Per-role monotonic counter for auto-assigned unique user codes.

Increments forever; numbers are never reused (deleting a user does not free
its code) so codes remain a stable confidential identifier.
"""
from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RoleCodeCounter(Base):
    __tablename__ = "role_code_counters"

    role: Mapped[str] = mapped_column(String(2), primary_key=True)
    next_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
