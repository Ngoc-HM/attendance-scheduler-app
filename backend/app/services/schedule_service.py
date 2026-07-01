"""Scheduling logic (F-07, F-08, F-09 + decision #8) — engine orchestration.

Bridges persistence and ``app.scheduler``: gather inputs → solve → persist
draft assignments / surface Violations (§5.6). Manual edits and approved
shift-changes are ALWAYS saved and re-checked (warnings, never blocks).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.i18n import t
from app.models.enums import AttendanceCode, ScheduleStatus, SwapKind
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.shift_change_request import ShiftChangeRequest
from app.models.user import User
from app.scheduler import SchedulerEngine
from app.scheduler.calendar_utils import build_weeks, month_days
from app.schemas.schedule import (
    ConstraintViolation,
    ManualOverrideRequest,
    MonthlyScheduleRead,
    ScheduleResult,
)
from app.services import flight_service, schedule_input_builder
from app.services.schedule_violation_checker import recheck


def get(db: Session, year: int, month: int, include_draft: bool) -> MonthlySchedule:
    """F-02 view. Non-admins see ONLY published schedules (G4 visibility)."""
    q = (
        db.query(MonthlySchedule)
        .options(selectinload(MonthlySchedule.assignments))
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
    )
    if not include_draft:
        q = q.filter(MonthlySchedule.status == ScheduleStatus.published)
    schedule = q.one_or_none()
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("schedule.not_found"))
    return schedule


def generate(db: Session, year: int, month: int, force: bool = False) -> ScheduleResult:
    """F-07 — build the monthly schedule via the CP-SAT engine (§5)."""
    existing = (
        db.query(MonthlySchedule)
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
        .one_or_none()
    )
    # Testing mode (owner 2026-07-01): admin may regenerate freely — no lock on
    # published schedules or manual overrides. Regenerating resets to draft.
    # ``force`` is kept in the signature for API compatibility but no longer gates.
    _ = force

    inp = schedule_input_builder.build(db, year, month)
    out = SchedulerEngine().solve(inp)
    if not out.feasible:  # only contradictory pins / timeout (§5.6 #12)
        return ScheduleResult(feasible=False, violations=_violations(out.violations))

    if existing is None:
        existing = MonthlySchedule(year=year, month=month)
        db.add(existing)
        db.flush()  # assign existing.id before deleting/inserting cells
    existing.status = ScheduleStatus.draft
    existing.generated_at = datetime.now(timezone.utc)

    # Hard-delete previous cells by schedule_id (business key) — the ORM
    # collection's id-based delete proved unreliable on regenerate (DELETE
    # matched 0 rows, then the re-insert collided on uq_assignment_cell).
    # Deleting by schedule_id + expiring the stale collection avoids the race.
    db.query(ShiftAssignment).filter(
        ShiftAssignment.schedule_id == existing.id
    ).delete(synchronize_session=False)
    db.flush()
    db.expire(existing, ["assignments"])

    for a in out.assignments:
        # Restore the concrete code on pinned cells: the engine plans approved
        # leave as X in the decision layer (§5.3 #5) — write the real AL/CD.
        code = inp.approved_off.get(a.user_id, {}).get(a.day, a.code)
        existing.assignments.append(
            ShiftAssignment(user_id=a.user_id, work_date=a.day, code=code)
        )
    db.commit()
    db.refresh(existing)
    return ScheduleResult(
        feasible=True,
        schedule=MonthlyScheduleRead.model_validate(existing),
        violations=_violations(out.violations),
    )


def manual_override(
    db: Session, schedule_id: int, payload: ManualOverrideRequest
) -> ScheduleResult:
    """F-09 — apply an admin edit; save ALWAYS, re-check, warn (§5.6 #14)."""
    schedule = _get_by_id(db, schedule_id)
    cell = next(
        (
            a
            for a in schedule.assignments
            if a.user_id == payload.user_id and a.work_date == payload.work_date
        ),
        None,
    )
    if cell is None:
        cell = ShiftAssignment(user_id=payload.user_id, work_date=payload.work_date)
        schedule.assignments.append(cell)
    cell.code = payload.code
    cell.is_manual_override = True
    db.commit()
    db.refresh(schedule)
    return ScheduleResult(
        feasible=True,
        schedule=MonthlyScheduleRead.model_validate(schedule),
        violations=_recheck_violations(db, schedule),
    )


def publish(db: Session, schedule_id: int) -> MonthlySchedule:
    """F-07 — draft → published; locks regeneration (not admin edits)."""
    schedule = _get_by_id(db, schedule_id)
    schedule.status = ScheduleStatus.published
    db.commit()
    db.refresh(schedule)
    return schedule


def apply_shift_change(db: Session, req: ShiftChangeRequest) -> list[str]:
    """Decision #8 — apply an approved change/swap to the schedule + re-check."""
    schedule = (
        db.query(MonthlySchedule)
        .options(selectinload(MonthlySchedule.assignments))
        .filter(
            MonthlySchedule.year == req.work_date.year,
            MonthlySchedule.month == req.work_date.month,
        )
        .one_or_none()
    )
    if schedule is None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("swap.no_schedule"))

    cells = {
        (a.user_id, a.work_date): a
        for a in schedule.assignments
        if a.work_date == req.work_date
    }
    mine = cells.get((req.requester_id, req.work_date))
    if mine is None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=t("swap.no_schedule"))

    if req.kind is SwapKind.change_code:
        mine.code = req.requested_code
        mine.is_manual_override = True
    else:  # swap_with — exchange the two users' codes for that date
        theirs = cells.get((req.counterpart_user_id, req.work_date))
        if theirs is None:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=t("swap.no_schedule"))
        mine.code, theirs.code = theirs.code, mine.code
        mine.is_manual_override = theirs.is_manual_override = True

    db.commit()
    return [f"{v.rule}: {v.message}" for v in _recheck_violations(db, schedule)]


# --- internals -------------------------------------------------------------

def _get_by_id(db: Session, schedule_id: int) -> MonthlySchedule:
    schedule = db.get(MonthlySchedule, schedule_id)
    if schedule is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("schedule.not_found"))
    return schedule


def _violations(items) -> list[ConstraintViolation]:
    return [
        ConstraintViolation(rule=v.rule, message=v.message, day=v.day, user_id=v.user_id)
        for v in items
    ]


def _recheck_violations(db: Session, schedule: MonthlySchedule) -> list[ConstraintViolation]:
    """Re-run the §5.3 checks over the persisted grid (F-09 warnings)."""
    days = month_days(schedule.year, schedule.month)
    users = db.query(User).filter(User.id.in_({a.user_id for a in schedule.assignments})).all()
    grid: dict[tuple[int, date], AttendanceCode] = {
        (a.user_id, a.work_date): a.code for a in schedule.assignments
    }
    warnings = recheck(
        grid=grid,
        roles={u.id: u.role for u in users},
        carry_streaks={u.id: u.carry_streak for u in users},
        weeks=build_weeks(days),
        flight_pairs=flight_service.flight_pairs_map(db, days),
    )
    return [ConstraintViolation(rule="manual_recheck", message=w) for w in warnings]
