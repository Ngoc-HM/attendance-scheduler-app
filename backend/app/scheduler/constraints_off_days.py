"""§5.3 #2 — two OFF (X) days per 7-day block (soft, decision #2/#4/#7).

Per person and per block (7-day groups anchored at day 1, decision #7) the
number of X days must equal a target:

    target = partial_block_off_target(len(block)) + approved-off days in block

Approved leave (AL/CD) is pinned as X in the decision layer (§5.3 #5) but does
NOT count toward the weekly off quota (decision #4) — raising the target by the
pin count guarantees the person still gets their genuine X days on top.

Soft: ``sum(X) + under - over == target`` with ``under``/``over`` penalized at
the slack weight, so an over-constrained block reports a Violation instead of
making the model infeasible.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.calendar_utils import partial_block_off_target
from app.scheduler.domain import SolverInput
from app.scheduler.slack_registry import SlackRegistry


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    for p in inp.people:
        pinned = inp.approved_off.get(p.user_id, {})
        for block in inp.weeks:
            pinned_in_block = sum(1 for d in block if d in pinned)
            target = partial_block_off_target(len(block)) + pinned_in_block

            label = f"off_{p.user_id}_{block[0].isoformat()}"
            under = model.NewIntVar(0, 9, f"{label}_under")
            over = model.NewIntVar(0, 9, f"{label}_over")

            model.Add(
                sum(x[(p.user_id, d, AttendanceCode.X)] for d in block)
                + under - over == target
            )

            registry.register(
                under,
                rule="two_days_off_per_week",
                message=(
                    f"User {p.user_id}: fewer than the required "
                    f"{target} off day(s) in block starting {block[0]}"
                ),
                day=block[0],
                user_id=p.user_id,
            )
            registry.register(
                over,
                rule="two_days_off_per_week",
                message=(
                    f"User {p.user_id}: more than the required "
                    f"{target} off day(s) in block starting {block[0]}"
                ),
                day=block[0],
                user_id=p.user_id,
            )
