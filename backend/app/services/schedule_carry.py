"""Carried cells of a schedule (owner 2026-11-18).

Generating month M also plans the days of M+1 up to the Sunday that ends
M's last week. Those cells are stored in M+1's schedule with ``carried``
set, so every month-scoped feature still finds a cell through its own
month. This module answers the questions the rest of the app asks about
them:

* a schedule whose cells are ALL carried counts as "not generated yet"
  (Generate needs no force, the dashboard and the autorun see no roster);
* a carried cell counts as published once the PREVIOUS month is published
  (the month that planned it): employees see it, and the time-clock board
  and the "today's shift" line read it, while its own month is a draft.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.enums import ScheduleStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.services.schedule_history import previous_month


def following_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def find(db: Session, year: int, month: int) -> MonthlySchedule | None:
    return (
        db.query(MonthlySchedule)
        .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
        .one_or_none()
    )


def _any(db: Session, schedule_id: int, carried: bool, *, overridden: bool = False) -> bool:
    q = db.query(ShiftAssignment.id).filter(
        ShiftAssignment.schedule_id == schedule_id,
        ShiftAssignment.carried.is_(carried),
    )
    if overridden:
        q = q.filter(ShiftAssignment.is_manual_override.is_(True))
    return q.first() is not None


def has_own_cells(db: Session, schedule_id: int) -> bool:
    """The month itself was generated (a cell that is not carried)."""
    return _any(db, schedule_id, False)


def is_carry_only(db: Session, schedule: MonthlySchedule | None) -> bool:
    """Only carried cells: the month is not generated yet."""
    return (
        schedule is not None
        and not has_own_cells(db, schedule.id)
        and _any(db, schedule.id, True)
    )


def is_generated(db: Session, schedule: MonthlySchedule | None) -> bool:
    """A roster exists for the month (a carry-only schedule does not count)."""
    return schedule is not None and not is_carry_only(db, schedule)


def has_overrides(db: Session, schedule_id: int, *, carried: bool) -> bool:
    """An admin edit among the schedule's own (or carried) cells."""
    return _any(db, schedule_id, carried, overridden=True)


def carried_cells(db: Session, schedule_id: int) -> list[ShiftAssignment]:
    return (
        db.query(ShiftAssignment)
        .filter(ShiftAssignment.schedule_id == schedule_id, ShiftAssignment.carried.is_(True))
        .order_by(ShiftAssignment.work_date, ShiftAssignment.user_id)
        .all()
    )


def previous_published(db: Session, year: int, month: int) -> bool:
    """The month before ``year/month`` is published (it planned the carried
    cells of ``year/month``)."""
    previous = find(db, *previous_month(year, month))
    return previous is not None and previous.status is ScheduleStatus.published


def published_cells(db: Session, schedule: MonthlySchedule | None) -> list[ShiftAssignment]:
    """The cells of ``schedule`` that count as the published roster."""
    if schedule is None:
        return []
    if schedule.status is ScheduleStatus.published:
        return list(schedule.assignments)
    if previous_published(db, schedule.year, schedule.month):
        return [a for a in schedule.assignments if a.carried]
    return []


def published_cell(db: Session, user_id: int, day: date) -> ShiftAssignment | None:
    """The person's published roster cell of ``day``, if any."""
    cell = (
        db.query(ShiftAssignment)
        .join(MonthlySchedule, ShiftAssignment.schedule_id == MonthlySchedule.id)
        .filter(ShiftAssignment.user_id == user_id, ShiftAssignment.work_date == day)
        .one_or_none()
    )
    if cell is None:
        return None
    if cell.schedule.status is ScheduleStatus.published:
        return cell
    if cell.carried and previous_published(db, day.year, day.month):
        return cell
    return None
