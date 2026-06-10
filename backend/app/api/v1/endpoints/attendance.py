"""Attendance recording endpoints (F-10, F-11, F-12)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, DbSession
from app.schemas.attendance import AttendanceRead, AttendanceUpsert

router = APIRouter()


@router.get("", response_model=list[AttendanceRead])
def list_attendance(db: DbSession, year: int, month: int):
    # TODO: delegate to attendance_service.list_month(db, year, month)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.put("", response_model=AttendanceRead)
def upsert_attendance(db: DbSession, payload: AttendanceUpsert, admin: AdminUser):
    """F-11/F-12 — admin records the actual daily code (incl. sick ``S``).

    Sick data is special-category (§9.1): restrict read access to admins.
    """
    # TODO: delegate to attendance_service.upsert(db, payload, recorded_by=admin.id)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("/sick-cover", response_model=AttendanceRead)
def handle_sick_cover(db: DbSession, payload: AttendanceUpsert, _admin: AdminUser):
    """F-10 — mark a sick day and assign A/D cover for the empty shift (§6)."""
    # TODO: delegate to attendance_service.handle_sick(db, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
