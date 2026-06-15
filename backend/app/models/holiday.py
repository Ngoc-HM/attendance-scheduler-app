"""Public holidays (spec §4.5 / F-13 — OVERRIDDEN by locked decision #5).

A holiday is a NORMAL WORKING DAY (owner decision 2026-06-11, diverges from
spec §7 "PH = X"). Holiday rows are *premium-off markers* only: an OFF day
landing on a holiday (like Sat/Sun) counts as a "premium off" and is balanced
fairly across people over months (decision #6). The scheduler never pins
these days off. See docs/design-decisions.md.
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
