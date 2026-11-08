"""Attendance recording endpoints (F-10, F-11, F-12).

Sick (S) is special-category health data (§9.1): writes are admin-only and
audited (phase 10); non-admin read paths mask S. RBAC hardening lands in
phase 10 — these handlers already guard mutations behind ``AdminUser``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.api.params import MonthQuery, YearQuery
from app.schemas.attendance import (
    AttendanceRead,
    AttendanceUpsert,
    SickCoverResult,
)
from app.services import attendance_service, audit_service

router = APIRouter()


@router.get("", response_model=list[AttendanceRead])
def list_attendance(db: DbSession, year: YearQuery, month: MonthQuery, _admin: AdminUser):
    """F-11 — actual attendance for a month. Admin-only: records may carry the
    sick code ``S``, which is special-category health data (§9.1)."""
    return attendance_service.list_month(db, year, month)


@router.get("/me", response_model=list[AttendanceRead])
def list_my_attendance(db: DbSession, year: YearQuery, month: MonthQuery, current_user: ActiveUser):
    """A user sees only their OWN month of records (§9.5 data minimization).

    Seeded rows mirror the plan, so they stay hidden while the month's
    schedule is not published (none, or a draft after a forced regenerate).
    """
    return attendance_service.list_own_month(db, current_user.id, year, month)


@router.post("/seed", response_model=dict)
def seed_from_schedule(db: DbSession, year: YearQuery, month: MonthQuery, admin: AdminUser):
    """Seed missing actuals from the PUBLISHED schedule and re-sync
    still-seeded cells (admin-recorded cells are never overwritten). A draft
    month answers 409 ``attendance.schedule_not_published``."""
    seeded = attendance_service.seed_from_schedule(db, year, month)
    audit_service.record(db, admin.id, "attendance.seed", "AttendanceRecord",
                         detail=f"{year}-{month:02d}: {seeded} cells")
    return {"seeded": seeded}


@router.put("", response_model=AttendanceRead)
def upsert_attendance(db: DbSession, payload: AttendanceUpsert, admin: AdminUser):
    """F-11/F-12 — admin records/updates the actual daily code."""
    record = attendance_service.upsert(db, payload, recorded_by=admin.id)
    # Audit every write; flag sick (S) explicitly — special-category (§9.1).
    action = "attendance.sick" if payload.code.value == "S" else "attendance.upsert"
    audit_service.record(db, admin.id, action, "AttendanceRecord", record.id,
                         detail=f"user={payload.user_id} {payload.work_date} {payload.code.value}")
    return record


@router.post("/sick-cover", response_model=SickCoverResult)
def handle_sick_cover(db: DbSession, payload: AttendanceUpsert, admin: AdminUser):
    """F-10 — mark a sick day and assign A/D cover for the dropped shift (§6)."""
    result = attendance_service.handle_sick(db, payload, recorded_by=admin.id)
    audit_service.record(db, admin.id, "attendance.sick", "AttendanceRecord",
                         result.sick.id, detail=f"user={payload.user_id} {payload.work_date}")
    return result
