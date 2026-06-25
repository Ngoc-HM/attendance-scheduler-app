"""Flight schemas (F-04, §8)."""

from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class FlightDayUpsert(BaseModel):
    day: date
    flight_pairs: int = Field(ge=0, le=2)  # 0 / 1 / 2 (§5.3 #4)


class FlightRead(ORMModel):
    id: int
    day: date
    flt_number: int
    route: str | None
    sta: time | None
    std: time | None


class FlightDayRead(ORMModel):
    id: int
    day: date
    flight_pairs: int
    # Flight legs for that day, ordered by flt_number (populated by endpoint).
    flights: list[FlightRead] = []


class FlightUpsert(BaseModel):
    day: date
    flt_number: int  # 37/36/31/30 (§8)
    route: str | None = None
    sta: time | None = None  # LT FRA
    std: time | None = None  # LT FRA


# ---------------------------------------------------------------------------
# Preset schemas
# ---------------------------------------------------------------------------


class FlightPresetUpsert(BaseModel):
    label: str
    route: str | None = None
    flt_arr: int
    flt_dep: int
    sta: time
    std: time
    sort_order: int = 0
    is_active: bool = True


class FlightPresetRead(ORMModel):
    id: int
    label: str
    route: str | None
    flt_arr: int
    flt_dep: int
    sta: time
    std: time
    sort_order: int
    is_active: bool


# ---------------------------------------------------------------------------
# Day-apply schema (replace a day's flights from selected presets)
# ---------------------------------------------------------------------------


class FlightDayApply(BaseModel):
    day: date
    # 0..2 preset IDs; empty list clears the day (flight_pairs → 0).
    preset_ids: list[int]


class FlightDayApplyBatch(BaseModel):
    # Ordered list of per-day apply items; processed atomically in one commit.
    items: list[FlightDayApply]
