"""GDPR / BDSG operational controls (spec §9.3, §9.5).

* ``purge_before`` — retention: delete personnel records older than a cutoff
  (data minimization, §26 BDSG). Guarded by a legal floor: German working-time
  records must be kept at least 24 months (ArbZG §16(2)).
* ``export_user_data`` — data-subject access / portability (GDPR Art. 15/20):
  everything the system holds about one person, as plain JSON. Never includes
  the password hash. Erasure is the existing admin ``DELETE /users/{id}``.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.business_time import business_today
from app.core.config import settings
from app.core.i18n import t
from app.models.attendance import AttendanceRecord
from app.models.audit import AuditLog
from app.models.leave import LeaveRequest
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.self_arrange_request import SelfArrangeRequest
from app.models.shift_change_request import ShiftChangeRequest
from app.models.time_clock import TimeClockEntry
from app.models.user import User

# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------

def _months_before(today: date, months: int) -> date:
    year = today.year
    month = today.month - months
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def default_cutoff(today: date | None = None) -> date:
    """First day of the month ``DATA_RETENTION_MONTHS`` before today."""
    return _months_before(today or business_today(), settings.DATA_RETENTION_MONTHS)


def purge_before(
    db: Session, cutoff: date | None = None, today: date | None = None
) -> tuple[date, dict[str, int]]:
    """Delete personnel records dated strictly before ``cutoff``.

    Returns ``(cutoff, {table: rows deleted})``. Raises 400 when the cutoff
    is more recent than the legal minimum retention.
    """
    today = today or business_today()
    cutoff = cutoff or default_cutoff(today)
    floor = _months_before(today, settings.DATA_RETENTION_MIN_MONTHS)
    if cutoff > floor:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=t("compliance.retention_too_short")
        )

    cutoff_dt = datetime.combine(cutoff, time.min)
    cutoff_month_index = cutoff.year * 12 + cutoff.month
    deleted: dict[str, int] = {}

    deleted["attendance_records"] = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.work_date < cutoff)
        .delete(synchronize_session=False)
    )
    deleted["time_clock_entries"] = (
        db.query(TimeClockEntry)
        .filter(TimeClockEntry.work_date < cutoff)
        .delete(synchronize_session=False)
    )
    deleted["shift_assignments"] = (
        db.query(ShiftAssignment)
        .filter(ShiftAssignment.work_date < cutoff)
        .delete(synchronize_session=False)
    )
    # Schedule headers whose month is entirely before the cutoff.
    old_schedules = [
        s
        for s in db.query(MonthlySchedule).all()
        if s.year * 12 + s.month < cutoff_month_index
    ]
    for s in old_schedules:
        db.delete(s)
    deleted["monthly_schedules"] = len(old_schedules)
    deleted["leave_requests"] = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.end_date < cutoff)
        .delete(synchronize_session=False)
    )
    deleted["shift_change_requests"] = (
        db.query(ShiftChangeRequest)
        .filter(ShiftChangeRequest.work_date < cutoff)
        .delete(synchronize_session=False)
    )
    old_self_arrange = [
        r
        for r in db.query(SelfArrangeRequest).all()
        if r.year * 12 + r.month < cutoff_month_index
    ]
    for r in old_self_arrange:
        db.delete(r)
    deleted["self_arrange_requests"] = len(old_self_arrange)
    deleted["audit_logs"] = (
        db.query(AuditLog)
        .filter(AuditLog.created_at < cutoff_dt)
        .delete(synchronize_session=False)
    )
    db.commit()
    return cutoff, deleted


# ---------------------------------------------------------------------------
# Data-subject export
# ---------------------------------------------------------------------------

def _plain(obj: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in fields:
        value = getattr(obj, name)
        if hasattr(value, "value") and not isinstance(value, datetime | date):
            value = value.value  # enums
        elif isinstance(value, datetime | date):
            value = value.isoformat()
        out[name] = value
    return out


def export_user_data(db: Session, user_id: int) -> dict[str, Any]:
    """All personal data held for ``user_id`` (Art. 15/20). No password hash."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))

    return {
        "exported_at": datetime.now(ZoneInfo(settings.TIMEZONE)).isoformat(timespec="seconds"),
        "profile": _plain(
            user,
            (
                "id", "username", "code", "full_name", "role", "status",
                "annual_leave_quota", "carry_comp", "carry_streak",
                "carry_premium_off", "created_at", "updated_at",
            ),
        ),
        "attendance_records": [
            _plain(r, ("work_date", "code", "note", "recorded_by"))
            for r in db.query(AttendanceRecord)
            .filter(AttendanceRecord.user_id == user_id)
            .order_by(AttendanceRecord.work_date)
        ],
        "schedule_cells": [
            _plain(a, ("work_date", "code", "is_manual_override"))
            for a in db.query(ShiftAssignment)
            .filter(ShiftAssignment.user_id == user_id)
            .order_by(ShiftAssignment.work_date)
        ],
        "leave_requests": [
            _plain(r, ("start_date", "end_date", "leave_type", "status", "note", "created_at"))
            for r in db.query(LeaveRequest)
            .filter(LeaveRequest.user_id == user_id)
            .order_by(LeaveRequest.start_date)
        ],
        "time_clock_entries": [
            _plain(e, ("work_date", "check_in_at", "check_out_at"))
            for e in db.query(TimeClockEntry)
            .filter(TimeClockEntry.user_id == user_id)
            .order_by(TimeClockEntry.work_date)
        ],
        "shift_change_requests": [
            _plain(
                r,
                (
                    "work_date", "kind", "requested_code", "counterpart_user_id",
                    "status", "note", "created_at",
                ),
            )
            for r in db.query(ShiftChangeRequest)
            .filter(
                or_(
                    ShiftChangeRequest.requester_id == user_id,
                    ShiftChangeRequest.counterpart_user_id == user_id,
                )
            )
            .order_by(ShiftChangeRequest.work_date)
        ],
        "self_arrange_requests": [
            {**_plain(r, ("year", "month", "status", "note", "created_at")), "changes": r.changes}
            for r in db.query(SelfArrangeRequest)
            .filter(SelfArrangeRequest.requester_id == user_id)
            .order_by(SelfArrangeRequest.created_at)
        ],
        "audit_actions_as_actor": [
            _plain(a, ("action", "entity", "entity_id", "detail", "created_at"))
            for a in db.query(AuditLog)
            .filter(AuditLog.actor_id == user_id)
            .order_by(AuditLog.created_at)
        ],
    }
