"""Flight schedule input (spec §4.2 / F-04, §8).

``FlightDay.flight_pairs`` (0/1/2) is the value the scheduler reads as
``flightPairs[d]`` to size the A1–A4 shift staffing (§5.3 #4). Individual
``Flight`` rows carry the detailed FLT number and STA/STD for display and
Excel import/export.
"""

from __future__ import annotations

from datetime import date, time

from sqlalchemy import Date, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class FlightDay(Base, TimestampMixin):
    __tablename__ = "flight_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, unique=True, index=True)
    # 0, 1 or 2 flight pairs that day — drives shift staffing (§5.3 #4).
    flight_pairs: Mapped[int] = mapped_column(Integer, default=0)


class Flight(Base, TimestampMixin):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    # FLT number convention (§8): 37=HAN-FRA, 36=reverse; 31=SGN-FRA, 30=reverse.
    flt_number: Mapped[int] = mapped_column(Integer)
    route: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # STA/STD in Frankfurt local time (LT FRA, §8).
    sta: Mapped[time | None] = mapped_column(Time, nullable=True)
    std: Mapped[time | None] = mapped_column(Time, nullable=True)
