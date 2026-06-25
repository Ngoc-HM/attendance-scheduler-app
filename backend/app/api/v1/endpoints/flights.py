"""Flight schedule endpoints (F-04, §8).

Supports manual entry, Excel import, preset CRUD, and preset-apply.

Route order matters — FastAPI matches in declaration order:
  /presets   and /days/apply are declared before any path-param routes
  to prevent shadowing.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.common import Message
from app.schemas.flight import (
    FlightDayApply,
    FlightDayApplyBatch,
    FlightDayRead,
    FlightDayUpsert,
    FlightPresetRead,
    FlightPresetUpsert,
    FlightRead,
    FlightUpsert,
)
from app.services import audit_service, flight_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Preset endpoints (static paths — declared first to avoid shadowing)
# ---------------------------------------------------------------------------


@router.get("/presets", response_model=list[FlightPresetRead])
def list_flight_presets(db: DbSession, _user: ActiveUser):
    """List all flight presets ordered by sort_order (any active user)."""
    return flight_service.list_presets(db)


@router.post("/presets", response_model=FlightPresetRead)
def create_flight_preset(db: DbSession, payload: FlightPresetUpsert, admin: AdminUser):
    """Create a new flight preset. Admin only."""
    preset = flight_service.create_preset(db, payload)
    audit_service.record(
        db, admin.id, "flight.preset.create", "FlightPreset",
        entity_id=preset.id, detail=preset.label,
    )
    return preset


@router.put("/presets/{preset_id}", response_model=FlightPresetRead)
def update_flight_preset(
    preset_id: int, db: DbSession, payload: FlightPresetUpsert, admin: AdminUser
):
    """Update an existing flight preset. Admin only."""
    preset = flight_service.update_preset(db, preset_id, payload)
    audit_service.record(
        db, admin.id, "flight.preset.update", "FlightPreset",
        entity_id=preset.id, detail=preset.label,
    )
    return preset


@router.delete("/presets/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flight_preset(preset_id: int, db: DbSession, admin: AdminUser):
    """Delete a flight preset. Admin only."""
    flight_service.delete_preset(db, preset_id)
    audit_service.record(
        db, admin.id, "flight.preset.delete", "FlightPreset",
        entity_id=preset_id,
    )


# ---------------------------------------------------------------------------
# Day-apply endpoint (static path — before any path-param routes)
# ---------------------------------------------------------------------------


@router.put("/days/apply", response_model=FlightDayRead)
def apply_presets_to_day(db: DbSession, payload: FlightDayApply, admin: AdminUser):
    """Replace a day's flights using selected preset IDs (0..2). Admin only.

    Empty preset_ids clears the day (flight_pairs → 0).
    The response includes the updated FlightDay with its Flight legs.
    """
    fd = flight_service.apply_presets_to_day(db, payload)
    audit_service.record(
        db, admin.id, "flight.day.apply", "FlightDay",
        entity_id=fd.id,
        detail=f"day={payload.day} preset_ids={payload.preset_ids}",
    )
    # Enrich with flight legs for the response.
    flights_map = flight_service.list_flights_for_days(db, [payload.day])
    return FlightDayRead(
        id=fd.id,
        day=fd.day,
        flight_pairs=fd.flight_pairs,
        flights=[FlightRead.model_validate(f) for f in flights_map.get(payload.day, [])],
    )


@router.put("/days/apply-batch", response_model=list[FlightDayRead])
def apply_presets_batch(db: DbSession, payload: FlightDayApplyBatch, admin: AdminUser):
    """Replace flights for multiple days atomically using preset IDs. Admin only.

    All items are applied in a single transaction.  Empty preset_ids for an
    item clears that day (flight_pairs → 0).  Returns list[FlightDayRead] in
    input order, each enriched with its Flight legs.
    """
    fds = flight_service.apply_presets_batch(db, payload)
    audit_service.record(
        db, admin.id, "flight.month.apply", "FlightDay",
        detail=f"{len(payload.items)} days",
    )

    # Enrich all affected days with their flight legs in one query.
    days = [fd.day for fd in fds]
    flights_map = flight_service.list_flights_for_days(db, days)

    return [
        FlightDayRead(
            id=fd.id,
            day=fd.day,
            flight_pairs=fd.flight_pairs,
            flights=[FlightRead.model_validate(f) for f in flights_map.get(fd.day, [])],
        )
        for fd in fds
    ]


# ---------------------------------------------------------------------------
# Day CRUD endpoints
# ---------------------------------------------------------------------------


@router.get("/days", response_model=list[FlightDayRead])
def list_flight_days(db: DbSession, _user: ActiveUser, year: int, month: int):
    """List all FlightDay records for the given year/month with flight legs."""
    days = flight_service.list_days(db, year, month)
    if not days:
        return []

    day_dates = [fd.day for fd in days]
    flights_map = flight_service.list_flights_for_days(db, day_dates)

    return [
        FlightDayRead(
            id=fd.id,
            day=fd.day,
            flight_pairs=fd.flight_pairs,
            flights=[FlightRead.model_validate(f) for f in flights_map.get(fd.day, [])],
        )
        for fd in days
    ]


@router.put("/days", response_model=FlightDayRead)
def upsert_flight_day(db: DbSession, payload: FlightDayUpsert, _admin: AdminUser):
    """Manual entry of flight-pair count for a day (0/1/2). Admin only."""
    fd = flight_service.upsert_day(db, payload)
    flights_map = flight_service.list_flights_for_days(db, [fd.day])
    return FlightDayRead(
        id=fd.id,
        day=fd.day,
        flight_pairs=fd.flight_pairs,
        flights=[FlightRead.model_validate(f) for f in flights_map.get(fd.day, [])],
    )


# ---------------------------------------------------------------------------
# Single flight CRUD + import
# ---------------------------------------------------------------------------


@router.put("", response_model=FlightRead)
def upsert_flight(db: DbSession, payload: FlightUpsert, _admin: AdminUser):
    """Manual entry of a single flight (FLT + STA/STD). Admin only."""
    return flight_service.upsert_flight(db, payload)


@router.post("/import", response_model=list[FlightRead])
def import_flights_excel(db: DbSession, file: UploadFile, admin: AdminUser):
    """F-04 — import the monthly flight list from an Excel (.xlsx) file.

    Expected columns (row 1 = header):
      A: date, B: flt_number, C: route, D: sta, E: std
    On any parse error the entire import is rejected (no partial commit).
    """
    flights = flight_service.import_excel(db, file)
    audit_service.record(
        db, admin.id, "flight.import", "Flight",
        detail=f"{len(flights)} flights from {file.filename}",
    )
    return flights
