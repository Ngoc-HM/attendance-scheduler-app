"""Attendance logic (F-10, F-11, F-12).

``AttendanceRecord`` is the ACTUAL daily code (vs the planned
``ShiftAssignment``). Admin records / updates each cell (F-11/F-12). On a sick
(S) day that drops a flight shift, an A/D backfill is selected (§6 / F-10) —
the just-sick person is forced to cover if a later colleague also goes sick.
"""

from __future__ import annotations

import calendar
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, Role
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.schemas.attendance import AttendanceUpsert, SickCoverResult
from app.services import sick_backfill


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def list_month(db: Session, year: int, month: int) -> list[AttendanceRecord]:
    first, last = _month_bounds(year, month)
    return (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.work_date >= first, AttendanceRecord.work_date <= last)
        .order_by(AttendanceRecord.work_date, AttendanceRecord.user_id)
        .all()
    )


def _get_cell(db: Session, user_id: int, day: date) -> AttendanceRecord | None:
    return (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.user_id == user_id, AttendanceRecord.work_date == day)
        .one_or_none()
    )


def upsert(db: Session, payload: AttendanceUpsert, recorded_by: int) -> AttendanceRecord:
    """F-11/F-12 — record/update the actual code for one (user, day)."""
    cell = _get_cell(db, payload.user_id, payload.work_date)
    if cell is None:
        cell = AttendanceRecord(user_id=payload.user_id, work_date=payload.work_date)
        db.add(cell)
    cell.code = payload.code
    cell.note = payload.note
    cell.recorded_by = recorded_by
    db.commit()
    db.refresh(cell)
    return cell


def seed_from_schedule(db: Session, year: int, month: int) -> int:
    """Copy a published schedule's cells into actuals (only missing ones).

    Gives the admin a starting point to adjust; never overwrites an existing
    actual record. Returns the number of cells seeded.
    """
    schedule = (
        db.query(MonthlySchedule)
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
        .one_or_none()
    )
    if schedule is None:
        return 0

    existing = {(r.user_id, r.work_date) for r in list_month(db, year, month)}
    seeded = 0
    for a in schedule.assignments:
        if (a.user_id, a.work_date) in existing:
            continue
        db.add(
            AttendanceRecord(user_id=a.user_id, work_date=a.work_date, code=a.code)
        )
        seeded += 1
    db.commit()
    return seeded


def actual_records_map(
    db: Session, year: int, month: int
) -> dict[tuple[int, date], AttendanceCode]:
    """{(user_id, day): code} of actuals — for calc (F-14) and reports (F-15)."""
    return {(r.user_id, r.work_date): r.code for r in list_month(db, year, month)}


def handle_sick(db: Session, payload: AttendanceUpsert, recorded_by: int) -> SickCoverResult:
    """F-10 / §6 — mark sick (S) and assign an A/D backfill for the lost shift.

    The dropped shift is read BEFORE overwriting with S (from the existing
    actual, falling back to the planned assignment). If it was a flight duty,
    a colleague is forced/chosen to take A/D cover (``sick_backfill``).
    """
    if payload.code is not AttendanceCode.S:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t("attendance.sick_only"))

    day = payload.work_date
    dropped = _planned_or_actual_code(db, payload.user_id, day)

    sick_record = upsert(db, payload, recorded_by)

    if not sick_backfill.needs_cover(dropped):
        return SickCoverResult(sick=sick_record, cover=None, message=None)

    proposal = sick_backfill.pick_candidate(
        sick_user_id=payload.user_id,
        day_codes=self_day_codes(db, day),
        roles=_roles(db),
        recently_sick=_recently_sick(db, year=day.year, month=day.month, before=day,
                                     exclude=payload.user_id),
        month_ad_counts=_month_ad_counts(db, day.year, day.month),
    )
    if proposal is None:
        return SickCoverResult(
            sick=sick_record, cover=None, message=t("attendance.sick_no_cover")
        )

    cover = upsert(
        db,
        AttendanceUpsert(
            user_id=proposal.user_id, work_date=day, code=proposal.new_code,
            note=proposal.reason,
        ),
        recorded_by,
    )
    return SickCoverResult(
        sick=sick_record, cover=cover, forced=proposal.forced, message=proposal.reason
    )


# --- pure-ish DB readers feeding sick_backfill -----------------------------

def _planned_or_actual_code(db: Session, user_id: int, day: date) -> AttendanceCode | None:
    actual = _get_cell(db, user_id, day)
    if actual is not None:
        return actual.code
    planned = (
        db.query(ShiftAssignment)
        .filter(ShiftAssignment.user_id == user_id, ShiftAssignment.work_date == day)
        .one_or_none()
    )
    return planned.code if planned else None


def self_day_codes(db: Session, day: date) -> dict[int, AttendanceCode]:
    """Each user's code for ``day`` — actual if present, else planned."""
    codes: dict[int, AttendanceCode] = {}
    for a in db.query(ShiftAssignment).filter(ShiftAssignment.work_date == day).all():
        codes[a.user_id] = a.code
    for r in db.query(AttendanceRecord).filter(AttendanceRecord.work_date == day).all():
        codes[r.user_id] = r.code  # actual overrides planned
    return codes


def _roles(db: Session) -> dict[int, Role]:
    return {u.id: u.role for u in db.query(User).all()}


def _recently_sick(
    db: Session, year: int, month: int, before: date, exclude: int
) -> list[int]:
    """User ids with an S earlier this month, most recent first (§6)."""
    first, _ = _month_bounds(year, month)
    rows = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.code == AttendanceCode.S,
            AttendanceRecord.work_date >= first,
            AttendanceRecord.work_date < before,
            AttendanceRecord.user_id != exclude,
        )
        .order_by(AttendanceRecord.work_date.desc())
        .all()
    )
    seen: list[int] = []
    for r in rows:
        if r.user_id not in seen:
            seen.append(r.user_id)
    return seen


def _month_ad_counts(db: Session, year: int, month: int) -> dict[int, int]:
    first, last = _month_bounds(year, month)
    rows = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.code == AttendanceCode.A_D,
            AttendanceRecord.work_date >= first,
            AttendanceRecord.work_date <= last,
        )
        .all()
    )
    counts: dict[int, int] = {}
    for r in rows:
        counts[r.user_id] = counts.get(r.user_id, 0) + 1
    return counts
