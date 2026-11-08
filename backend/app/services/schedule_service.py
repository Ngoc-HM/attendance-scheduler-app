"""Scheduling logic (F-07, F-08, F-09 + decision #8) — engine orchestration.

Bridges persistence and ``app.scheduler``: gather inputs → solve → persist
draft assignments / surface Violations (§5.6). Valid manual edits and approved
shift-changes are saved and re-checked (warnings do not discard the edit).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

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
from app.services import (
    attendance_service,
    flight_service,
    leave_service,
    role_code_validation,
    schedule_history,
    schedule_input_builder,
)
from app.services.schedule_violation_checker import recheck


def mask_sick_for_viewer(
    schedule: MonthlyScheduleRead, viewer_id: int
) -> MonthlyScheduleRead:
    """§9.1 — hide other people's sickness from a non-admin viewer.

    Any ``S`` cell that does not belong to ``viewer_id`` is returned as ``X``
    (an off day, which is what colleagues legitimately need to know). Own
    cells are untouched. Pure function over the read model.
    """
    masked = [
        a.model_copy(update={"code": AttendanceCode.X})
        if a.code is AttendanceCode.S and a.user_id != viewer_id
        else a
        for a in schedule.assignments
    ]
    return schedule.model_copy(update={"assignments": masked})


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
    """F-07 — build the monthly schedule via the CP-SAT engine (§5).

    Regenerating a published month, or one with manual edits, would wipe the
    edits and reset it to draft — refused (409) unless ``force`` is set.
    """
    existing = (
        db.query(MonthlySchedule)
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
        .one_or_none()
    )
    if existing is not None and not force:
        if existing.status is ScheduleStatus.published:
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail=t("schedule.published_locked")
            )
        # Query, not ``existing.assignments``: loading the collection here would
        # leave stale cells in the session ahead of the delete/re-insert below.
        has_overrides = (
            db.query(ShiftAssignment.id)
            .filter(
                ShiftAssignment.schedule_id == existing.id,
                ShiftAssignment.is_manual_override.is_(True),
            )
            .first()
            is not None
        )
        if has_overrides:
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail=t("schedule.has_overrides")
            )

    inp = schedule_input_builder.build(db, year, month)
    out = SchedulerEngine().solve(inp)
    if not out.feasible:  # only contradictory pins / timeout (§5.6 #12)
        return ScheduleResult(feasible=False, violations=_violations(out.violations))

    if existing is None:
        existing = MonthlySchedule(year=year, month=month)
        db.add(existing)
        db.flush()  # assign existing.id before deleting/inserting cells
    existing.status = ScheduleStatus.draft
    existing.generated_at = datetime.now(UTC)

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
    """F-09 — validate and apply an admin edit, then re-check and warn."""
    schedule = _get_by_id(db, schedule_id)
    if (
        payload.work_date.year != schedule.year
        or payload.work_date.month != schedule.month
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Override date must belong to the schedule month.",
        )
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
    # Planned grid: S is never allowed here (§9.1 — sickness lives in actuals).
    role_code_validation.validate_planned(user.role, payload.code)
    cell = next(
        (
            a
            for a in schedule.assignments
            if a.user_id == payload.user_id and a.work_date == payload.work_date
        ),
        None,
    )
    if cell is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Schedule cell not found.",
        )
    cell.code = payload.code
    cell.is_manual_override = True
    if schedule.status is ScheduleStatus.published:
        attendance_service.sync_planned_cell(db, cell.user_id, cell.work_date, cell.code)
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
    # Published assignments become the actual-attendance baseline: missing
    # actuals are seeded and still-seeded ones re-synced (re-publish after a
    # regenerate); admin-recorded actuals are never overwritten.
    attendance_service.seed_from_schedule(db, schedule.year, schedule.month)
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

    changed = [mine]
    if req.kind is SwapKind.change_code:
        requester = db.get(User, req.requester_id)
        if requester is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
        if req.requested_code is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="A requested code is required for a code change.",
            )
        # Re-checked here too: a request filed before the rule existed must
        # not slip an AL/CD/admin code through approval.
        role_code_validation.validate_requestable(requester.role, req.requested_code)
        mine.code = req.requested_code
        mine.is_manual_override = True
    else:  # swap_with — exchange the two users' codes for that date
        if req.counterpart_user_id is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("swap.counterpart_required")
            )
        theirs = cells.get((req.counterpart_user_id, req.work_date))
        if theirs is None:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=t("swap.no_schedule"))
        requester = db.get(User, req.requester_id)
        counterpart = db.get(User, req.counterpart_user_id)
        if requester is None or counterpart is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))
        # Each person's resulting code must be one they could request: a swap
        # must not hand over leave (AL), a comp day (CD) or an admin code.
        role_code_validation.validate_requestable(requester.role, theirs.code)
        role_code_validation.validate_requestable(counterpart.role, mine.code)
        mine.code, theirs.code = theirs.code, mine.code
        mine.is_manual_override = theirs.is_manual_override = True
        changed.append(theirs)

    if schedule.status is ScheduleStatus.published:
        for cell in changed:
            attendance_service.sync_planned_cell(db, cell.user_id, cell.work_date, cell.code)
    db.commit()
    return [f"{v.rule}: {v.message}" for v in _recheck_violations(db, schedule)]


def apply_leave_span(
    db: Session,
    user_id: int,
    start: date,
    end: date,
    code: AttendanceCode,
    *,
    only_if: AttendanceCode | None = None,
    skip: AttendanceCode | None = None,
) -> list[str]:
    """B4 — write a leave decision (AL approve / X revoke) into generated months.

    Regenerating would wipe manual edits, so the user's cells in every month
    of the span that already has a schedule get the code directly (published
    months also move their still-seeded actuals). ``only_if`` limits the write
    to cells currently holding that code: revoke passes AL, so a cell the
    admin re-coded after approval (or a CD) stays. ``skip`` leaves cells
    holding that code alone: approve passes X, so the weekly off days stay X
    (leave does not replace them, decision #4). A month without a schedule
    needs nothing: it reads approved leave when generated. Returns [] when no
    cell changed; otherwise the ``leave.schedule_applied`` notice, a note per
    month not generated yet, then each changed month's re-check warnings.
    Does not commit.
    """
    span = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    days = set(span)
    updated: list[MonthlySchedule] = []
    not_generated: list[str] = []
    for year, month in sorted({(d.year, d.month) for d in span}):
        schedule = (
            db.query(MonthlySchedule)
            .options(selectinload(MonthlySchedule.assignments))
            .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
            .one_or_none()
        )
        if schedule is None:
            not_generated.append(f"{year}-{month:02d}: {t('leave.schedule_not_generated')}")
            continue
        changed = [
            cell
            for cell in schedule.assignments
            if cell.user_id == user_id
            and cell.work_date in days
            and cell.code is not code
            and (only_if is None or cell.code is only_if)
            and (skip is None or cell.code is not skip)
        ]
        for cell in changed:
            cell.code = code
            if schedule.status is ScheduleStatus.published:
                attendance_service.sync_planned_cell(db, user_id, cell.work_date, code)
        if changed:
            updated.append(schedule)
    if not updated:
        return []
    db.flush()  # a later month's re-check reads the edited earlier month
    warnings = [t("leave.schedule_applied"), *not_generated]
    for schedule in updated:
        warnings += [
            f"{schedule.year}-{schedule.month:02d}: {v.message}"
            for v in _recheck_violations(db, schedule)
        ]
    return warnings


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
    """Re-run every engine rule over the persisted grid (F-09 warnings).

    Carry values (streak, comp) come from the same effective history the
    engine used (``schedule_history``), so the recheck and the generator
    agree on the month boundary.
    """
    days = month_days(schedule.year, schedule.month)
    users = db.query(User).filter(User.id.in_({a.user_id for a in schedule.assignments})).all()
    grid: dict[tuple[int, date], AttendanceCode] = {
        (a.user_id, a.work_date): a.code for a in schedule.assignments
    }
    boundary = schedule_history.build_boundary_states(
        db, users, schedule.year, schedule.month
    )
    warnings = recheck(
        grid=grid,
        roles={u.id: u.role for u in users},
        carry_streaks={uid: state.carry_streak for uid, state in boundary.items()},
        weeks=build_weeks(days),
        flight_pairs=flight_service.flight_pairs_map(db, days),
        previous_working={
            user_id: state.previous_working for user_id, state in boundary.items()
        },
        carry_comps={uid: state.carry_comp for uid, state in boundary.items()},
        annual_off=leave_service.annual_off_dates(db, schedule.year, schedule.month),
        prev_codes={uid: state.prev_codes for uid, state in boundary.items()},
    )
    return [ConstraintViolation(rule="manual_recheck", message=w) for w in warnings]
