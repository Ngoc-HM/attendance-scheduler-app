"""Flight schedule logic (F-04, §8).

Both manual entry and Excel import feed ``FlightDay.flight_pairs``, the
scheduler's ``flightPairs[d]`` input.
"""

from __future__ import annotations

from datetime import date

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.flight import Flight, FlightDay
from app.schemas.flight import FlightDayUpsert, FlightUpsert


def list_days(db: Session, year: int, month: int) -> list[FlightDay]:
    raise NotImplementedError  # TODO


def upsert_day(db: Session, payload: FlightDayUpsert) -> FlightDay:
    """Set the flight-pair count (0/1/2) for a day."""
    raise NotImplementedError  # TODO


def upsert_flight(db: Session, payload: FlightUpsert) -> Flight:
    raise NotImplementedError  # TODO


def import_excel(db: Session, file: UploadFile) -> list[Flight]:
    """F-04 — parse the monthly flight Excel (openpyxl) and upsert rows +
    derive ``flight_pairs`` per day."""
    raise NotImplementedError  # TODO


def flight_pairs_map(db: Session, days: list[date]) -> dict[date, int]:
    """Helper for the scheduler: ``{day: flight_pairs}`` (defaults 0)."""
    raise NotImplementedError  # TODO
