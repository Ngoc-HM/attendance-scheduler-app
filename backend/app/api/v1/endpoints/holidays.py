"""Public holiday endpoints (F-13).

Holidays are NORMAL working days (decision #5) — premium-off markers only,
never auto-pinned off.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.attendance import HolidayRead, HolidayUpsert
from app.services import audit_service, holiday_service

router = APIRouter()


@router.get("", response_model=list[HolidayRead])
def list_holidays(db: DbSession, year: int, _user: ActiveUser):
    return holiday_service.list_year(db, year)


@router.put("", response_model=HolidayRead)
def upsert_holiday(db: DbSession, payload: HolidayUpsert, admin: AdminUser):
    """F-13 — admin adds/renames a public holiday (premium-off marker)."""
    holiday = holiday_service.upsert(db, payload)
    audit_service.record(db, admin.id, "holiday.upsert", "Holiday", holiday.id,
                         detail=f"{payload.day} {payload.name}")
    return holiday


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holiday(db: DbSession, holiday_id: int, admin: AdminUser):
    holiday_service.delete(db, holiday_id)
    audit_service.record(db, admin.id, "holiday.delete", "Holiday", holiday_id)
