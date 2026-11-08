"""Two-phase solve (review C1/F4): slack first, then the soft objectives.

A single combined objective on a 1-CPU machine used to stop at the time limit
with 7–14 invented slack units although a clean schedule exists (a slack-only
solve proves 0 in a fraction of a second). Phase 1 now minimises slack alone,
phase 2 keeps that slack and works on the soft terms; the output reports the
solver status and whether the slack total is proven minimal.
"""

from __future__ import annotations

from datetime import date

from app.core.config import settings
from app.models.enums import Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days


def _review_instance(max_solve_seconds: float) -> SolverInput:
    """The 9-user December instance the review reproduced C1 with.

    1 M, 2 T, 1 F, 5 A; one flight pair Mon–Thu, two Fri–Sun; small carries;
    25/26 December are holidays.
    """
    days = month_days(2026, 12)
    roles = [Role.M] + [Role.T] * 2 + [Role.F] + [Role.A] * 5
    people = [
        PersonInput(
            uid,
            role,
            carry_comp=1 if uid % 3 == 0 else 0,
            carry_streak=uid % 4,
            carry_premium_off=uid % 3,
        )
        for uid, role in enumerate(roles, start=1)
    ]
    return SolverInput(
        year=2026,
        month=12,
        people=people,
        days=days,
        weeks=build_weeks(days),
        flight_pairs={d: (2 if d.weekday() in (4, 5, 6) else 1) for d in days},
        holidays={date(2026, 12, 25), date(2026, 12, 26)},
        max_solve_seconds=max_solve_seconds,
    )


def _small_instance() -> SolverInput:
    days = month_days(2026, 6)[:14]
    people = [PersonInput(1, Role.T)] + [PersonInput(u, Role.A) for u in (6, 7, 8)]
    return SolverInput(
        year=2026,
        month=6,
        people=people,
        days=days,
        weeks=build_weeks(days),
        flight_pairs={d: 1 for d in days},
        max_solve_seconds=10.0,
    )


def test_one_worker_finds_zero_slack(monkeypatch) -> None:
    """A single search worker (busy CI box / 1-CPU server) must not invent
    violations: the instance has a clean schedule."""
    monkeypatch.setattr(settings, "SOLVER_NUM_WORKERS", 1)
    out = SchedulerEngine().solve(_review_instance(max_solve_seconds=8.0))

    assert out.feasible
    assert out.violations == []
    assert out.slack_proven_minimal is True
    assert out.status in ("optimal", "feasible")


def test_status_reported() -> None:
    out = SchedulerEngine(num_workers=1).solve(_small_instance())

    assert out.feasible
    assert out.status == "optimal"
    assert out.slack_proven_minimal is True


def test_same_input_same_output_with_fixed_workers() -> None:
    """Same input, same plan (§5.6) when the worker count is fixed."""

    def grid(out):
        return sorted((a.user_id, a.day, a.code.value) for a in out.assignments)

    first = SchedulerEngine(num_workers=1).solve(_small_instance())
    second = SchedulerEngine(num_workers=1).solve(_small_instance())

    assert grid(first) == grid(second)
    assert [v.message for v in first.violations] == [v.message for v in second.violations]
