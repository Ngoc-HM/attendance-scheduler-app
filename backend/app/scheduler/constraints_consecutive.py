"""§5.3 #3 + §5.5 — no more than 5 consecutive working days (soft).

Two pieces per person:

1. Sliding window: every 6 consecutive days must contain at least one OFF —
   ``sum(works over 6 days) <= 5 + slack``.
2. Month boundary (§5.5): a run of ``carry_streak`` working days continues
   from last month, so the person may work at most ``5 - carry_streak`` more
   days before an OFF. Among the first ``max(1, 6 - carry_streak)`` days there
   must be at least one OFF (soft, same slack treatment).

"Working" here = any code in the person's role domain that is NOT a rest code
(X / CD).  Per role:

    Role.A → working = {A, D, A/D}
    Role.T → working = {AD}
    Role.M → working = {O/D}

This makes the consecutive rule role-safe: only vars that actually exist for
the person are referenced.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import OFF_CODES, codes_for
from app.scheduler.slack_registry import SlackRegistry

WINDOW = 6  # a 6-day all-working window is the smallest violation (§5.3 #3)


def _works(
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    user_id: int,
    d: date,
    person_codes: tuple[AttendanceCode, ...],
) -> cp_model.LinearExpr:
    """1 if the person works on ``d`` (any non-rest code from their domain), else 0."""
    return sum(
        x[(user_id, d, c)] for c in person_codes if c not in OFF_CODES
    )


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    days = sorted(inp.days)

    for p in inp.people:
        person_codes = codes_for(p.role)

        # --- 1. Sliding 6-day windows inside the month --------------------
        for i in range(len(days) - WINDOW + 1):
            window = days[i : i + WINDOW]
            slack = model.NewIntVar(
                0, 1, f"streak_{p.user_id}_{window[0].isoformat()}"
            )
            model.Add(
                sum(_works(x, p.user_id, d, person_codes) for d in window)
                <= WINDOW - 1 + slack
            )
            registry.register(
                slack,
                rule="max_consecutive_working",
                message=(
                    f"User {p.user_id}: more than 5 consecutive working days "
                    f"in the window starting {window[0]}"
                ),
                day=window[0],
                user_id=p.user_id,
            )

        # --- 2. Carry-over from last month (§5.5) -------------------------
        if p.carry_streak > 0:
            # At most (5 - carry_streak) further working days, so at least
            # one OFF among the first (6 - carry_streak) days (min 1 day).
            k = max(1, WINDOW - p.carry_streak)
            head = days[:k]
            slack = model.NewIntVar(0, 1, f"carry_{p.user_id}")
            model.Add(
                sum(_works(x, p.user_id, d, person_codes) for d in head)
                <= len(head) - 1 + slack
            )
            registry.register(
                slack,
                rule="max_consecutive_working_carry",
                message=(
                    f"User {p.user_id}: run of {p.carry_streak} working days "
                    f"from last month not broken within the first {k} day(s)"
                ),
                day=head[0],
                user_id=p.user_id,
            )
