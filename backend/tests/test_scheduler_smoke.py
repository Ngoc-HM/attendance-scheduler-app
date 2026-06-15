"""Smoke test for the scheduler engine wiring (§5).

Builds a tiny feasible instance (no flight pairs, no constraints beyond
'one status per day' + 'respect approved off') and checks the engine returns a
feasible assignment for every (person, day). The richer constraints (§5.3
#2–#4) are scaffolded; extend this test as they are implemented.
"""

from __future__ import annotations

from app.models.enums import Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days


def test_engine_returns_one_status_per_cell() -> None:
    days = month_days(2026, 6)
    people = [
        PersonInput(user_id=1, role=Role.A),
        PersonInput(user_id=2, role=Role.T),
    ]
    inp = SolverInput(
        year=2026,
        month=6,
        people=people,
        days=days,
        weeks=build_weeks(days),
        flight_pairs={d: 0 for d in days},
        max_solve_seconds=5.0,
    )

    out = SchedulerEngine().solve(inp)

    assert out.feasible
    # Exactly one assignment per (person, day).
    assert len(out.assignments) == len(people) * len(days)
