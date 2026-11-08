"""Attendance logic (F-10, F-11, F-12).

``AttendanceRecord`` is the ACTUAL daily code (vs the planned
``ShiftAssignment``). Admin records / updates each cell (F-11/F-12). On a sick
(S) day that drops a flight shift, an A/D backfill is selected (§6 / F-10) —
the just-sick person is forced to cover if a later colleague also goes sick.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, Role, ScheduleStatus, UserStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.schemas.attendance import AttendanceRead, AttendanceUpsert, SickCoverResult
from app.services import role_code_validation, sick_backfill

# §6 recently-sick memory: an S within this many days before the new sick day
# makes that person the forced A/D cover — a rolling window, so a sickness on
# the last days of one month still counts early the next month.
RECENTLY_SICK_LOOKBACK_DAYS = 30


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


def list_own_month(
    db: Session, user_id: int, year: int, month: int
) -> list[AttendanceRecord]:
    """One user's actuals for ``/attendance/me``.

    A seeded row (``recorded_by`` NULL) is a copy of the plan, so it is only
    shown while the month's schedule is PUBLISHED: after a forced regenerate
    the seeded rows follow the draft and must not leak unpublished codes.
    Admin-recorded rows and sick days (always a real record) stay visible.
    """
    published = (
        db.query(MonthlySchedule.id)
        .filter(
            MonthlySchedule.year == year,
            MonthlySchedule.month == month,
            MonthlySchedule.status == ScheduleStatus.published,
        )
        .first()
        is not None
    )
    first, last = _month_bounds(year, month)
    rows = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.user_id == user_id,
            AttendanceRecord.work_date >= first,
            AttendanceRecord.work_date <= last,
        )
        .order_by(AttendanceRecord.work_date)
        .all()
    )
    return [
        r
        for r in rows
        if published or r.recorded_by is not None or r.code is AttendanceCode.S
    ]


def _get_cell(db: Session, user_id: int, day: date) -> AttendanceRecord | None:
    return (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.user_id == user_id, AttendanceRecord.work_date == day)
        .one_or_none()
    )


def upsert(db: Session, payload: AttendanceUpsert, recorded_by: int) -> AttendanceRecord:
    """F-11/F-12 — record/update the actual code for one (user, day)."""
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
    role_code_validation.validate(user.role, payload.code)
    cell = _get_cell(db, payload.user_id, payload.work_date)
    if cell is None:
        cell = AttendanceRecord(user_id=payload.user_id, work_date=payload.work_date)
        db.add(cell)
    cell.code = payload.code
    # §9.1 — never persist free text alongside a sick day: no medical detail,
    # whatever the client sent. Other codes keep their optional note.
    cell.note = None if payload.code is AttendanceCode.S else payload.note
    cell.recorded_by = recorded_by
    db.commit()
    db.refresh(cell)
    return cell


def seed_from_schedule(db: Session, year: int, month: int) -> int:
    """Copy a schedule's cells into actuals as the admin's starting point.

    Only a PUBLISHED schedule is copied: actuals are readable by the employee
    (``/attendance/me``), so seeding a draft would leak unpublished codes —
    a draft answers 409 ``attendance.schedule_not_published``. ``publish()``
    flips the status before it calls this, so publishing still seeds.

    Missing actuals are inserted; actuals still as seeded (``recorded_by``
    NULL) are re-synced to the roster, so publishing a regenerated month
    refreshes them (B5). An admin-recorded actual is never overwritten.
    Returns the number of cells inserted.
    """
    schedule = (
        db.query(MonthlySchedule)
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
        .one_or_none()
    )
    if schedule is None:
        return 0
    if schedule.status is not ScheduleStatus.published:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=t("attendance.schedule_not_published")
        )

    existing = {(r.user_id, r.work_date): r for r in list_month(db, year, month)}
    seeded = 0
    for a in schedule.assignments:
        cell = existing.get((a.user_id, a.work_date))
        if cell is None:
            db.add(
                AttendanceRecord(user_id=a.user_id, work_date=a.work_date, code=a.code)
            )
            seeded += 1
        else:
            follow_plan(cell, a.code)
    db.commit()
    return seeded


def sync_planned_cell(
    db: Session, user_id: int, work_date: date, code: AttendanceCode
) -> bool:
    """Carry an edit of a roster cell into its seeded actual (B5, I1).

    Draft or published: a draft can still hold actuals seeded while it was
    published (forced regenerate), and the next month's boundary reads them.
    Never inserts a row, so a never-published draft gains no actuals.

    Only an actual nobody recorded by hand (``recorded_by`` NULL, i.e. left as
    ``seed_from_schedule`` wrote it) follows the plan; an admin-recorded cell
    always wins. Does not commit. Returns True when the actual was updated.
    """
    cell = _get_cell(db, user_id, work_date)
    return cell is not None and follow_plan(cell, code)


def follow_plan(cell: AttendanceRecord, code: AttendanceCode) -> bool:
    """Set a still-seeded actual (``recorded_by`` NULL) to the planned code.

    A sick day (S) never follows the plan, whoever recorded it: the planned
    grid can never hold S (§9.1), so an S actual is always a real record —
    e.g. one whose recorder was deleted before decision #39 kept it attributed.
    """
    if cell.recorded_by is not None or cell.code is AttendanceCode.S:
        return False
    cell.code = code
    return True


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

    sick_record = AttendanceRead.model_validate(upsert(db, payload, recorded_by))

    if not sick_backfill.needs_cover(dropped):
        return SickCoverResult(sick=sick_record, cover=None, message=None)

    proposal = sick_backfill.pick_candidate(
        sick_user_id=payload.user_id,
        day_codes=self_day_codes(db, day),
        roles=_roles(db),
        recently_sick=_recently_sick(db, before=day, exclude=payload.user_id),
        month_ad_counts=_month_ad_counts(db, day.year, day.month),
    )
    if proposal is None:
        return SickCoverResult(
            sick=sick_record, cover=None, message=t("attendance.sick_no_cover")
        )

    # §9.1 — the cover row is the colleague's ordinary actual; a note such as
    # "recently sick" would put health data on it, so it carries none. The
    # reason goes to the admin in the response only.
    cover = AttendanceRead.model_validate(
        upsert(
            db,
            AttendanceUpsert(
                user_id=proposal.user_id, work_date=day, code=proposal.new_code,
                note=None,
            ),
            recorded_by,
        )
    )
    return SickCoverResult(
        sick=sick_record, cover=cover, forced=proposal.forced,
        message=t(proposal.reason_key),
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
    """Roles of ACTIVE users only — a disabled or pending account is never
    picked as A/D cover (B6)."""
    rows = db.query(User.id, User.role).filter(User.status == UserStatus.active).all()
    return {uid: role for uid, role in rows}


def _recently_sick(db: Session, before: date, exclude: int) -> list[int]:
    """User ids with an S in the 30 days before ``before``, most recent first (§6).

    The window rolls across month boundaries (not "since the 1st").
    """
    since = before - timedelta(days=RECENTLY_SICK_LOOKBACK_DAYS)
    rows = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.code == AttendanceCode.S,
            AttendanceRecord.work_date >= since,
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
