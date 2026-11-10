"""No more than 5 consecutive OFF days (soft) — customer rule 2026-06-12.

A break of MORE than 5 consecutive off days is, by policy, annual leave (it
must be registered the prior year). So the scheduler keeps ordinary off-runs
to at most 5 in a row: every window of 6 consecutive days must contain at
least one working day.

Every rest code in the person's domain counts as OFF (``OFF_CODES`` ∩
``codes_for(role)``): weekly X, approved leave (pinned as ``X`` in the
decision layer) AND the comp days (CD) the solver places itself — matching
the post-edit recheck in ``schedule_violation_checker.check_off_chain``.

A window that holds approved leave is EXEMPT (ruling R1, 2026-11-08): a
pinned leave day of this month (``inp.approved_off`` — annual or monthly AL),
an approved annual-leave day (``inp.long_leave_off``), or an AL among the
previous month's codes. So the weekly X days next to a leave are legal, while
six ordinary off days in a row are still flagged even right after a leave.

The windows reach back into the previous month through
``PersonInput.prev_codes`` (oldest first, ending on its last day): those days
are fixed facts, so a window with a worked day there can never be all off.

Soft + slack, consistent with the always-feasible architecture (decision #2):
an unavoidable long off-run still returns a schedule plus a Violation.
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import OFF_CODES, codes_for
from app.scheduler.slack_registry import SlackRegistry

WINDOW = 6  # a 6-day all-off window is the smallest violation (> 5 off)


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    days = sorted(inp.days)
    if not days:
        return

    for p in inp.people:
        # Role F is T-like (owner 2026-07-22): the max-5-consecutive-OFF rule
        # applies to F exactly as it does to T.
        leave = set(inp.approved_off.get(p.user_id, {})) | inp.long_leave_off.get(
            p.user_id, set()
        )
        off_codes = [c for c in codes_for(p.role) if c in OFF_CODES]

        # Only the last WINDOW-1 previous days can share a window with this month.
        prev = list(p.prev_codes)[-(WINDOW - 1) :]
        timeline: list[tuple[date, AttendanceCode | None]] = [
            (days[0] - timedelta(days=len(prev) - i), code) for i, code in enumerate(prev)
        ]
        timeline += [(d, None) for d in days]  # None = decided by the solver

        for i in range(len(timeline) - WINDOW + 1):
            window = timeline[i : i + WINDOW]
            fixed = [code for _, code in window if code is not None]
            current = [d for d, code in window if code is None]
            # A worked previous day breaks the run; leave makes it legal (R1).
            if any(code.is_working or code is AttendanceCode.AL for code in fixed):
                continue
            if any(d in leave for d in current):
                continue
            start = window[0][0]
            slack = model.new_int_var(0, 1, f"offchain_{p.user_id}_{start.isoformat()}")
            # At least one of this month's days in the window is a working day.
            model.add(
                sum(x[(p.user_id, d, c)] for d in current for c in off_codes)
                <= len(current) - 1 + slack
            )
            registry.register(
                slack,
                rule="max_consecutive_off",
                message=(
                    f"User {p.user_id}: more than 5 consecutive OFF days "
                    f"in the window starting {start} — such a break must "
                    f"be registered as annual leave"
                ),
                day=start,
                user_id=p.user_id,
                params={"start": start},
            )
