"""Attendance logic (F-10, F-11, F-12)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.attendance import AttendanceRecord
from app.schemas.attendance import AttendanceUpsert


def list_month(db: Session, year: int, month: int) -> list[AttendanceRecord]:
    raise NotImplementedError  # TODO


def upsert(db: Session, payload: AttendanceUpsert, recorded_by: int) -> AttendanceRecord:
    """F-11/F-12 — record the actual daily code; stamp ``recorded_by`` (admin)."""
    raise NotImplementedError  # TODO


def handle_sick(db: Session, payload: AttendanceUpsert) -> AttendanceRecord:
    """F-10 / §6 — mark sick (``S``) and ensure an A/D covers the empty shift.

    Priority: someone who was just sick is forced to take A/D cover if a later
    sick day occurs."""
    raise NotImplementedError  # TODO
