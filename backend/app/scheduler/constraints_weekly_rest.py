"""Legacy calendar-week helpers retained for compatibility.

Weekly work quotas no longer apply. Monthly entitlement and max-five
consecutive work rules are wired by ``constraints.add_all`` instead.
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.slack_registry import SlackRegistry

MAX_WORKING = 5


def weeks(days: list[date]) -> list[tuple[date, list[date], list[date]]]:
    """(Monday, days before the month, days of the month) for each Mon–Sun
    week touching ``days`` (sorted, contiguous). Shared with the re-check."""
    days = sorted(days)
    if not days:
        return []
    first_monday = days[0] - timedelta(days=days[0].weekday())
    before = [first_monday + timedelta(days=n) for n in range(days[0].weekday())]
    out: list[tuple[date, list[date], list[date]]] = []
    for day in days:
        if day.weekday() == 0 or not out:
            monday = day - timedelta(days=day.weekday())
            out.append((monday, before if not out else [], []))
        out[-1][2].append(day)
    return out


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    """Compatibility no-op: no calendar-week work quota."""
    return None
