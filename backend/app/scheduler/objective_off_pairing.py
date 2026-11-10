"""§5.4 #8 (partial revival) — pair each week's OFF (X) days ADJACENTLY (soft).

Owner decision 2026-07-01: bring back the "2 weekly off days should sit next to
each other" preference — BUT WITHOUT the weekend bias (T7+CN). The 2026-06-18
call still stands for weekends: Sat/Sun are ordinary working days and the offs
must not pile onto the weekend (that fairness is handled by ``premium_off``).
This objective only rewards *adjacency*, not *which* days.

Low weight on purpose: it yields to every hard/high-priority rule — flight
staffing (§5.3 #4, slack 10 000), comp days (2 000), A/D balance (100) and
premium-off fairness (30). So it never breaks 1A+2D / 1A+1D staffing, the
max-5-consecutive-working rule, or the 2-X-per-week quota; it only shapes the
placement of the offs once those are satisfied.

The partial block after the 28th has no off quota (owner 2026-11-10), so there
is nothing to pair there and it is skipped.

Model (per person, per full 7-day block with an off target ``k`` >= 2):
    both[i] = X[day_i] AND X[day_{i+1}]           (consecutive OFF pair)
    a fully-clustered block yields ``k - 1`` such pairs; penalise the shortfall
        penalty = weight * ((k - 1) - sum(both))
For a normal 2-off block this is ``weight * (1 - is_adjacent)`` — zero when the
two offs are next to each other, ``weight`` when they are split apart.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.calendar_utils import block_off_target
from app.scheduler.domain import SolverInput


def terms(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    weight: int,
) -> list[cp_model.LinearExpr]:
    """Return adjacency-shortfall penalties (every role has X + a block quota)."""
    penalties: list[cp_model.LinearExpr] = []

    for p in inp.people:
        pinned = inp.approved_off.get(p.user_id, {})
        for block in inp.weeks:
            base = block_off_target(len(block))
            if base is None:
                continue  # leftover days: no quota → nothing to pair
            target = base + sum(1 for d in block if d in pinned)

            both: list[cp_model.IntVar] = []
            for i in range(len(block) - 1):
                xa = x[(p.user_id, block[i], AttendanceCode.X)]
                xb = x[(p.user_id, block[i + 1], AttendanceCode.X)]
                b = model.new_bool_var(
                    f"pairoff_{p.user_id}_{block[i].isoformat()}"
                )
                # b == (xa AND xb)
                model.add(b <= xa)
                model.add(b <= xb)
                model.add(b >= xa + xb - 1)
                both.append(b)

            # Shortfall of adjacent pairs vs the fully-clustered ideal (k - 1).
            penalties.append(weight * ((target - 1) - cp_model.LinearExpr.sum(both)))

    return penalties
