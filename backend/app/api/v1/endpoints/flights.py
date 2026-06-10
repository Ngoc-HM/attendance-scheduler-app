"""Flight schedule endpoints (F-04, §8).

Supports both manual entry and Excel import (spec §4.2 [CHỐT]).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import AdminUser, DbSession
from app.schemas.flight import (
    FlightDayRead,
    FlightDayUpsert,
    FlightRead,
    FlightUpsert,
)

router = APIRouter()


@router.get("/days", response_model=list[FlightDayRead])
def list_flight_days(db: DbSession, year: int, month: int):
    # TODO: delegate to flight_service.list_days(db, year, month)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.put("/days", response_model=FlightDayRead)
def upsert_flight_day(db: DbSession, payload: FlightDayUpsert, _admin: AdminUser):
    """Manual entry of flight-pair count for a day (0/1/2)."""
    # TODO: delegate to flight_service.upsert_day(db, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.put("", response_model=FlightRead)
def upsert_flight(db: DbSession, payload: FlightUpsert, _admin: AdminUser):
    """Manual entry of a single flight (FLT + STA/STD)."""
    # TODO: delegate to flight_service.upsert_flight(db, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("/import", response_model=list[FlightRead])
def import_flights_excel(db: DbSession, file: UploadFile, _admin: AdminUser):
    """F-04 — import the monthly flight list from an Excel file."""
    # TODO: delegate to flight_service.import_excel(db, file)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
