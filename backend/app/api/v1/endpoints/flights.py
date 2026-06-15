"""Flight schedule endpoints (F-04, §8).

Supports both manual entry and Excel import (spec §4.2 [CHỐT]).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.flight import (
    FlightDayRead,
    FlightDayUpsert,
    FlightRead,
    FlightUpsert,
)
from app.services import audit_service, flight_service

router = APIRouter()


@router.get("/days", response_model=list[FlightDayRead])
def list_flight_days(db: DbSession, _user: ActiveUser, year: int, month: int):
    """List all FlightDay records for the given year/month (any active user)."""
    return flight_service.list_days(db, year, month)


@router.put("/days", response_model=FlightDayRead)
def upsert_flight_day(db: DbSession, payload: FlightDayUpsert, _admin: AdminUser):
    """Manual entry of flight-pair count for a day (0/1/2). Admin only."""
    return flight_service.upsert_day(db, payload)


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
    audit_service.record(db, admin.id, "flight.import", "Flight",
                         detail=f"{len(flights)} flights from {file.filename}")
    return flights
