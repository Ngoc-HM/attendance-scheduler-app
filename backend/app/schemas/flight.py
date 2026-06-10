"""Flight schemas (F-04, §8)."""

from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class FlightDayUpsert(BaseModel):
    day: date
    flight_pairs: int = Field(ge=0, le=2)  # 0 / 1 / 2 (§5.3 #4)


class FlightDayRead(ORMModel):
    id: int
    day: date
    flight_pairs: int


class FlightUpsert(BaseModel):
    day: date
    flt_number: int  # 37/36/31/30 (§8)
    route: str | None = None
    sta: time | None = None  # LT FRA
    std: time | None = None  # LT FRA


class FlightRead(ORMModel):
    id: int
    day: date
    flt_number: int
    route: str | None
    sta: time | None
    std: time | None
