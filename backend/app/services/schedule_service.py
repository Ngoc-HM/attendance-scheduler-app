"""Scheduling logic (F-07, F-08, F-09 + decision #8) — engine orchestration.

Bridges persistence and ``app.scheduler``: gather inputs → solve → persist
draft assignments / surface Violations (§5.6). Valid manual edits and approved
shift-changes are saved and re-checked (warnings do not discard the edit).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core.business_time import business_today
from app.core.i18n import t
from app.models.enums import AttendanceCode, ScheduleStatus, SwapKind, UserStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.shift_change_request import ShiftChangeRequest
from app.models.user import User
from app.scheduler import SchedulerEngine
from app.scheduler.calendar_utils import month_days
from app.scheduler.domain import Violation
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
from app.services.schedule_violation_text import render_all


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
    Regenerating a month that already had a schedule also moves the actuals
    still as seeded from the old roster (``recorded_by`` NULL) onto the new
    plan — whether the old roster is published or a draft that was published
    before — so neither attendance nor the next month's boundary state keeps
    reading the replaced plan; admin-recorded actuals stay. ``/attendance/me``
    hides seeded rows while the month is a draft.
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
        return ScheduleResult(feasible=False, violations=_violations(db, out.violations))

    # Any earlier schedule may have left seeded actuals: a published one, or a
    # draft that was published before a forced regenerate.
    had_schedule = existing is not None
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

    plan: dict[tuple[int, date], AttendanceCode] = {}
    for a in out.assignments:
        # Restore the concrete code on pinned cells: the engine plans approved
        # leave as X in the decision layer (§5.3 #5) — write the real AL/CD.
        code = inp.approved_off.get(a.user_id, {}).get(a.day, a.code)
        plan[(a.user_id, a.day)] = code
        existing.assignments.append(
            ShiftAssignment(user_id=a.user_id, work_date=a.day, code=code)
        )
    if had_schedule:
        _resync_seeded_actuals(db, year, month, plan)
    db.commit()
    db.refresh(existing)
    return ScheduleResult(
        feasible=True,
        schedule=MonthlyScheduleRead.model_validate(existing),
        violations=_violations(db, out.violations),
    )


def manual_override(
    db: Session, schedule_id: int, payload: ManualOverrideRequest
) -> ScheduleResult:
    """F-09 — validate and apply an admin edit, then re-check and warn.

    R4 — a user activated after the month was generated has no row: the edit
    creates the missing cell for an ACTIVE user (on a published month its
    actual is seeded too). A missing cell of a pending/disabled user is 404.
    """
    schedule = _get_by_id(db, schedule_id)
    if (
        payload.work_date.year != schedule.year
        or payload.work_date.month != schedule.month
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=t("schedule.override_date_out_of_month"),
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
    created = cell is None
    if cell is None:
        if user.status is not UserStatus.active:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail=t("schedule.cell_not_found")
            )
        cell = ShiftAssignment(user_id=payload.user_id, work_date=payload.work_date)
        schedule.assignments.append(cell)
    cell.code = payload.code
    cell.is_manual_override = True
    if not created:
        # Every edit moves a still-seeded actual, draft or published: a draft
        # can carry actuals seeded before a forced regenerate, and the next
        # month's boundary reads them. sync_planned_cell never inserts.
        attendance_service.sync_planned_cell(db, cell.user_id, cell.work_date, cell.code)
    db.commit()
    if schedule.status is ScheduleStatus.published and created:
        # The new cell has no actual yet: seed it like publishing would.
        attendance_service.seed_from_schedule(db, schedule.year, schedule.month)
    db.refresh(schedule)
    return ScheduleResult(
        feasible=True,
        schedule=MonthlyScheduleRead.model_validate(schedule),
        violations=_recheck_violations(db, schedule),
    )


def violations_for(db: Session, schedule_id: int) -> list[ConstraintViolation]:
    """C2 — the month's hard-rule check, on demand (admin view / pre-publish).

    Same list a manual edit returns (``_recheck_violations``), so an autorun
    draft's problems are visible before anyone edits or publishes it.
    """
    return _recheck_violations(db, _get_by_id(db, schedule_id))


def publish(db: Session, schedule_id: int) -> MonthlySchedule:
    """F-07 — draft → published; locks regeneration (not admin edits).

    Publishing with violations stays allowed (admin decision): the client
    reads ``violations_for`` first and asks the admin to confirm.
    """
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
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("swap.code_required")
            )
        # Re-checked here too: a request filed before the rule existed must
        # not slip an AL/CD/admin code through approval.
        role_code_validation.validate_requestable(requester.role, req.requested_code)
        # B4: the cell may have become leave (AL), a comp day (CD), sickness or
        # an admin code since the request was filed — those are not re-coded
        # by request (the AL would still count against the quota).
        if mine.code not in role_code_validation.requestable_codes(requester.role):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("swap.cell_locked")
            )
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
        if counterpart.status is not UserStatus.active:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail=t("swap.counterpart_inactive")
            )
        # Each person's resulting code must be one they could request: a swap
        # must not hand over leave (AL), a comp day (CD) or an admin code.
        role_code_validation.validate_requestable(requester.role, theirs.code)
        role_code_validation.validate_requestable(counterpart.role, mine.code)
        mine.code, theirs.code = theirs.code, mine.code
        mine.is_manual_override = theirs.is_manual_override = True
        changed.append(theirs)

    # Draft or published: a still-seeded actual follows the edit (I1).
    for cell in changed:
        attendance_service.sync_planned_cell(db, cell.user_id, cell.work_date, cell.code)
    # No commit: the caller commits the cells together with the request's
    # status (one transaction under the request's row lock).
    db.flush()
    # Rendered text only (the rule id is not for people to read).
    return [v.message for v in _recheck_violations(db, schedule)]


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
    of the span that already has a schedule get the code directly (and their
    still-seeded actuals follow, draft or published). ``only_if`` limits the write
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


def _violations(db: Session, items: list[Violation]) -> list[ConstraintViolation]:
    """Solver violations in the request's language, people by code and name."""
    ids = {v.user_id for v in items if v.user_id is not None}
    users = db.query(User).filter(User.id.in_(ids)).all() if ids else []
    return render_all(items, {u.id: u for u in users})


def _resync_seeded_actuals(
    db: Session, year: int, month: int, plan: dict[tuple[int, date], AttendanceCode]
) -> None:
    """F11 — move still-seeded actuals of the month onto a regenerated plan.

    ``attendance_service.follow_plan`` keeps the seed rule in one place: only
    an actual nobody recorded by hand (and never a sick day) follows the plan.
    A seeded actual of a user the new plan no longer has (disabled since)
    keeps its old code — harmless: the boundary state and reports read active
    users only. One SELECT for the whole month (M1), not one per row.
    Does not commit.
    """
    for record in attendance_service.list_month(db, year, month):
        code = plan.get((record.user_id, record.work_date))
        if code is not None:
            attendance_service.follow_plan(record, code)


def _recheck_violations(db: Session, schedule: MonthlySchedule) -> list[ConstraintViolation]:
    """Re-run every engine rule over the persisted grid (F-09 warnings).

    Carry values (streak, comp) come from the same effective history the
    engine used (``schedule_history``), so the recheck and the generator
    agree on the month boundary.

    R4 — only ACTIVE users get the per-person rules. A user disabled after
    generation keeps their cells: those dated before ``business_today()`` were
    really worked, so they stay ordinary cover and are not flagged (I2); from
    today on each working cell they still hold is flagged
    (``disabled_user_duty``) and no longer counts as cover, so the admin
    re-plans it.
    """
    days = month_days(schedule.year, schedule.month)
    today = business_today()
    users = db.query(User).filter(User.id.in_({a.user_id for a in schedule.assignments})).all()
    active = [u for u in users if u.status is UserStatus.active]
    inactive_ids = {u.id for u in users if u.status is not UserStatus.active}
    grid: dict[tuple[int, date], AttendanceCode] = {
        (a.user_id, a.work_date): a.code
        for a in schedule.assignments
        if a.user_id not in inactive_ids or a.work_date < today
    }
    inactive_duty = [
        Violation(
            day=a.work_date,
            user_id=a.user_id,
            rule="disabled_user_duty",
            # The rendered text starts with the day, like the staffing lines,
            # so the text-only callers (shift change, leave, self-arrange)
            # show it.
            message=f"{a.work_date}: disabled user still on duty ({a.code.value})",
            params={"code": a.code.value},
        )
        for a in sorted(schedule.assignments, key=lambda a: (a.work_date, a.user_id))
        if a.user_id in inactive_ids and a.work_date >= today and a.code.is_working
    ]
    boundary = schedule_history.build_boundary_states(
        db, active, schedule.year, schedule.month
    )
    warnings = recheck(
        grid=grid,
        roles={u.id: u.role for u in active},
        carry_streaks={uid: state.carry_streak for uid, state in boundary.items()},
        days=days,
        flight_pairs=flight_service.flight_pairs_map(db, days),
        previous_working={
            user_id: state.previous_working for user_id, state in boundary.items()
        },
        carry_comps={uid: state.carry_comp for uid, state in boundary.items()},
        annual_off=leave_service.annual_off_dates(db, schedule.year, schedule.month),
        prev_codes={uid: state.prev_codes for uid, state in boundary.items()},
        # Disabled users' past cells (kept in ``grid``) count as cover only.
        cover_roles={u.id: u.role for u in users if u.id in inactive_ids},
    )
    # Real rule names, day and user_id (the client only shows ``message``),
    # text in the request's language.
    return render_all(inactive_duty + warnings, {u.id: u for u in users})
