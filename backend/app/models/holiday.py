"""Public holidays (spec §4.5 / F-13).

A holiday counts as an OFF day (code ``X``). Admin maintains this list; the
scheduler treats these days like approved time off (§5.3 #5).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Holiday(Base, TimestampMixin):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
