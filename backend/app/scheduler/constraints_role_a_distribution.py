"""Minimum monthly A-duty exposure for each fixed role-A person."""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput
from app.scheduler.slack_registry import SlackRegistry

MIN_A_DAYS = 2
MIN_FULL_MONTH_DAYS = 28


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    # Unit tests and diagnostic solves sometimes pass a partial month slice. The
    # business requirement applies to an actual full monthly roster only.
    if len(inp.days) < MIN_FULL_MONTH_DAYS:
        return

    for person in inp.people:
        if person.role is not Role.A:
            continue
        pure_a_days = sum(
            x[(person.user_id, day, AttendanceCode.A)] for day in inp.days
        )
        under = model.NewIntVar(0, MIN_A_DAYS, f"min_a_under_{person.user_id}")
        model.Add(pure_a_days + under >= MIN_A_DAYS)
        registry.register(
            under,
            rule="role_a_minimum_a_days",
            message=(
                f"User {person.user_id}: fewer than {MIN_A_DAYS} A-duty days "
                "in the month"
            ),
            user_id=person.user_id,
        )
