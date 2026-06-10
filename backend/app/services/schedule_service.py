"""Scheduling logic (F-07, F-08, F-09) — orchestrates the OR-Tools engine.

This service is the bridge between persistence and ``app.scheduler``:
gather inputs (people, days, flight pairs, approved leave, holidays,
carry-over) → build ``SolverInput`` → run ``SchedulerEngine`` → persist the
``ShiftAssignment`` rows / surface violations.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.schedule import MonthlySchedule
from app.schemas.schedule import ManualOverrideRequest, ScheduleResult


def get(db: Session, year: int, month: int) -> MonthlySchedule:
    raise NotImplementedError  # TODO


def generate(db: Session, year: int, month: int) -> ScheduleResult:
    """F-07 — build the monthly schedule.

    Outline:
        1. Load active users, the month's days, ``flight_pairs`` per day,
           approved leave, holidays, and per-user ``carry_comp``/``carry_streak``.
        2. Build ``app.scheduler.domain.SolverInput``.
        3. ``SchedulerEngine().solve(input)`` (§5.3 hard, §5.4 soft).
        4. If feasible: persist ``ShiftAssignment`` rows (status=draft).
           Else: return ``feasible=False`` + violations (§5.6).
    """
    raise NotImplementedError  # TODO


def manual_override(
    db: Session, schedule_id: int, payload: ManualOverrideRequest
) -> ScheduleResult:
    """F-09 — apply an admin edit and re-check hard constraints (§5.3).

    The edit is always saved (``is_manual_override=True``) but any resulting
    violation is returned so the admin can confirm (§5.6 #14)."""
    raise NotImplementedError  # TODO


def publish(db: Session, schedule_id: int) -> MonthlySchedule:
    raise NotImplementedError  # TODO
