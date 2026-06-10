"""Auto-scheduling endpoints — the core feature (F-07, F-08, F-09, §5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, DbSession
from app.schemas.schedule import (
    GenerateScheduleRequest,
    ManualOverrideRequest,
    MonthlyScheduleRead,
    ScheduleResult,
)

router = APIRouter()


@router.get("/{year}/{month}", response_model=MonthlyScheduleRead)
def get_schedule(db: DbSession, year: int, month: int):
    # TODO: delegate to schedule_service.get(db, year, month)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("/generate", response_model=ScheduleResult)
def generate_schedule(db: DbSession, payload: GenerateScheduleRequest, _admin: AdminUser):
    """F-07 — run the OR-Tools engine to build the monthly schedule (§5).

    Returns ``feasible=False`` plus the violated constraints when no valid
    solution exists (§5.6).
    """
    # TODO: delegate to schedule_service.generate(db, payload.year, payload.month)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("/{schedule_id}/override", response_model=ScheduleResult)
def manual_override(db: DbSession, schedule_id: int, payload: ManualOverrideRequest, _admin: AdminUser):
    """F-09 — admin edits a cell; response warns of any hard-constraint break."""
    # TODO: delegate to schedule_service.manual_override(db, schedule_id, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("/{schedule_id}/publish", response_model=MonthlyScheduleRead)
def publish_schedule(db: DbSession, schedule_id: int, _admin: AdminUser):
    # TODO: delegate to schedule_service.publish(db, schedule_id)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
