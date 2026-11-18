"""Shift time frames (decision #71): everyone reads, the admin sets A and D.

Store and display only; the check-in/out logic never reads these times.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.shift_time import ShiftTimeRead, ShiftTimesUpdate, ShiftToday
from app.services import audit_service, shift_time_service

router = APIRouter()


@router.get("", response_model=list[ShiftTimeRead])
def list_shift_times(db: DbSession, _user: ActiveUser):
    """A and D as set by the admin, plus the derived A/D frame."""
    return shift_time_service.list_frames(db)


@router.put("", response_model=list[ShiftTimeRead])
def update_shift_times(db: DbSession, payload: ShiftTimesUpdate, admin: AdminUser):
    frames = shift_time_service.update(db, payload)
    audit_service.record(
        db, admin.id, "shift_time.update", "ShiftTime",
        detail=" ".join(f"{f.code} {f.start}-{f.end}" for f in payload.frames),
    )
    return frames


@router.get("/today", response_model=ShiftToday)
def my_shift_today(db: DbSession, current_user: ActiveUser):
    """The caller's code today with its frame (time-clock page)."""
    return shift_time_service.today_for_user(db, current_user.id)
