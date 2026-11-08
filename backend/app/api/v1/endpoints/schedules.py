"""Auto-scheduling endpoints — the core feature (F-07, F-08, F-09, §5)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.api.params import MonthPath, YearPath
from app.core.business_time import business_today
from app.core.config import settings
from app.core.i18n import t
from app.schemas.schedule import (
    GenerateScheduleRequest,
    ManualOverrideRequest,
    MonthlyScheduleRead,
    ScheduleResult,
)
from app.services import audit_service, schedule_service

router = APIRouter()


@router.get("/{year}/{month}", response_model=MonthlyScheduleRead)
def get_schedule(db: DbSession, year: YearPath, month: MonthPath, current_user: ActiveUser):
    """View the month's schedule. Drafts are visible to admins only (G4).

    Non-admin visibility window (owner 2026-07-09): any past month, the current
    month, and at most 2 months ahead — published months only, as before.

    §9.1 — a non-admin never sees a colleague's sickness: the planned grid
    rejects S on write, and any legacy S cell of ANOTHER user is masked as X
    on read (defense in depth). A person's own cells are returned unchanged.
    """
    is_admin = current_user.role.is_admin
    if not is_admin and settings.ENVIRONMENT != "dev":
        today = business_today()
        if year * 12 + month > today.year * 12 + today.month + 2:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail=t("schedule.month_out_of_range")
            )
    schedule = MonthlyScheduleRead.model_validate(
        schedule_service.get(db, year, month, include_draft=is_admin)
    )
    if not is_admin:
        schedule = schedule_service.mask_sick_for_viewer(schedule, current_user.id)
    return schedule


@router.post("/generate", response_model=ScheduleResult)
def generate_schedule(
    db: DbSession, payload: GenerateScheduleRequest, admin: AdminUser
):
    """F-07 — run the OR-Tools engine to build the monthly schedule (§5).

    Always returns a complete draft plus any rule Violations for the admin to
    resolve (§5.6 — always-feasible slack architecture, decision #2).
    409 when the month is published or has manual edits and ``force`` is unset.
    """
    result = schedule_service.generate(db, payload.year, payload.month, payload.force)
    # The force flag is part of the trail: a forced run drops manual edits
    # and un-publishes the month.
    audit_service.record(db, admin.id, "schedule.generate", "MonthlySchedule",
                         detail=f"{payload.year}-{payload.month:02d} force={payload.force}")
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
