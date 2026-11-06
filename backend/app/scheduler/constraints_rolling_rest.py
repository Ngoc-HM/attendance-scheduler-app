"""At least two rest days in every rolling seven calendar days.

Unlike the legacy 1-7 / 8-14 block quota, these windows cross both block and
month boundaries.  The six preceding days are fixed facts supplied through
``SolverInput.previous_working``; current-month days are solver expressions.
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import OFF_CODES, codes_for
from app.scheduler.slack_registry import SlackRegistry

WINDOW = 7
MAX_WORKING = 5


def _current_working(
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    user_id: int,
    day: date,
    role_codes: tuple[AttendanceCode, ...],
) -> cp_model.LinearExpr | int:
    return sum(x[(user_id, day, code)] for code in role_codes if code not in OFF_CODES)


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    days = sorted(inp.days)
    if not days:
        return

    previous_days = [days[0] - timedelta(days=n) for n in range(6, 0, -1)]

    for person in inp.people:
        fixed = inp.previous_working.get(person.user_id, {})
        role_codes = codes_for(person.role)
        timeline: list[tuple[date, int | cp_model.LinearExpr]] = [
            (day, int(fixed.get(day, False))) for day in previous_days
        ]
        timeline.extend(
            (day, _current_working(x, person.user_id, day, role_codes))
            for day in days
        )

        for start in range(len(timeline) - WINDOW + 1):
            window = timeline[start : start + WINDOW]
            # Windows ending before this month contain no decision variable and
            # are the previous month's responsibility.
            if window[-1][0] < days[0]:
                continue
            slack = model.new_int_var(
                0, 2, f"rolling7_{person.user_id}_{window[0][0].isoformat()}"
            )
            model.add(sum(value for _, value in window) <= MAX_WORKING + slack)
            registry.register(
                slack,
                rule="rolling_seven_min_two_rest",
                message=(
                    f"User {person.user_id}: fewer than 2 rest days in the "
                    f"7-day window starting {window[0][0]}"
                ),
                day=window[0][0],
                user_id=person.user_id,
            )
