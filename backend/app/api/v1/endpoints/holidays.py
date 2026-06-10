"""Public holiday endpoints (F-13)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, DbSession
from app.schemas.attendance import HolidayRead, HolidayUpsert

router = APIRouter()


@router.get("", response_model=list[HolidayRead])
def list_holidays(db: DbSession, year: int):
    # TODO: delegate to holiday_service.list_year(db, year)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.put("", response_model=HolidayRead)
def upsert_holiday(db: DbSession, payload: HolidayUpsert, _admin: AdminUser):
    """F-13 — admin adds a public holiday (counts as OFF day ``X``)."""
    # TODO: delegate to holiday_service.upsert(db, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(db: DbSession, holiday_id: int, _admin: AdminUser):
    # TODO: delegate to holiday_service.delete(db, holiday_id)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
