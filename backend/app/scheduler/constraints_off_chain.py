"""No more than 5 consecutive OFF days (soft) — customer rule 2026-06-12.

A break of MORE than 5 consecutive off days is, by policy, annual leave (it
must be registered the prior year). So the scheduler keeps ordinary off-runs
(weekly X + monthly leave / CD, all rendered as ``X`` in the decision layer)
to at most 5 in a row: every window of 6 consecutive days must contain at
least one working day.

Approved ANNUAL leave (``inp.long_leave_off``) is the sanctioned long break —
any 6-day window touching it is EXEMPT, so a legitimately-registered 7-day
holiday is not flagged.

Soft + slack, consistent with the always-feasible architecture (decision #2):
an unavoidable long off-run still returns a schedule plus a Violation.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.slack_registry import SlackRegistry

WINDOW = 6  # a 6-day all-off window is the smallest violation (> 5 off)


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    days = sorted(inp.days)

    for p in inp.people:
        annual = inp.long_leave_off.get(p.user_id, set())
        for i in range(len(days) - WINDOW + 1):
            window = days[i : i + WINDOW]
            # Exempt windows overlapping a sanctioned annual-leave block.
            if any(d in annual for d in window):
                continue
            slack = model.NewIntVar(
                0, 1, f"offchain_{p.user_id}_{window[0].isoformat()}"
            )
            # At most 5 of the 6 days may be OFF (X) → at least one working day.
            model.Add(
                sum(x[(p.user_id, d, AttendanceCode.X)] for d in window)
                <= WINDOW - 1 + slack
            )
            registry.register(
                slack,
                rule="max_consecutive_off",
                message=(
                    f"User {p.user_id}: more than 5 consecutive OFF days "
                    f"in the window starting {window[0]} — such a break must "
                    f"be registered as annual leave"
                ),
                day=window[0],
                user_id=p.user_id,
            )
