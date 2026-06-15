"""Auto-scheduling endpoints — the core feature (F-07, F-08, F-09, §5)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.schedule import (
    GenerateScheduleRequest,
    ManualOverrideRequest,
    MonthlyScheduleRead,
    ScheduleResult,
)
from app.services import audit_service, schedule_service

router = APIRouter()


@router.get("/{year}/{month}", response_model=MonthlyScheduleRead)
def get_schedule(db: DbSession, year: int, month: int, current_user: ActiveUser):
    """View the month's schedule. Drafts are visible to admins only (G4)."""
    return schedule_service.get(
        db, year, month, include_draft=current_user.role.is_admin
    )


@router.post("/generate", response_model=ScheduleResult)
def generate_schedule(
    db: DbSession, payload: GenerateScheduleRequest, admin: AdminUser
):
    """F-07 — run the OR-Tools engine to build the monthly schedule (§5).

    Always returns a complete draft plus any rule Violations for the admin to
    resolve (§5.6 — always-feasible slack architecture, decision #2).
    """
    result = schedule_service.generate(db, payload.year, payload.month, payload.force)
    audit_service.record(db, admin.id, "schedule.generate", "MonthlySchedule",
                         detail=f"{payload.year}-{payload.month:02d}")
    return result


@router.post("/{schedule_id}/override", response_model=ScheduleResult)
def manual_override(
    db: DbSession, schedule_id: int, payload: ManualOverrideRequest, admin: AdminUser
):
    """F-09 — admin edits a cell; saved ALWAYS, hard-rule warnings returned."""
    result = schedule_service.manual_override(db, schedule_id, payload)
    audit_service.record(db, admin.id, "schedule.override", "ShiftAssignment", schedule_id,
                         detail=f"user={payload.user_id} {payload.work_date} {payload.code.value}")
    return result


@router.post("/{schedule_id}/publish", response_model=MonthlyScheduleRead)
def publish_schedule(db: DbSession, schedule_id: int, admin: AdminUser):
    """Draft → published; locks regeneration and reveals the month to users."""
    schedule = schedule_service.publish(db, schedule_id)
    audit_service.record(db, admin.id, "schedule.publish", "MonthlySchedule", schedule_id)
    return schedule
