"""§5.3 #4 + #6 — daily flight-shift staffing from flight pairs (soft floor).

Per-day MINIMUM coverage required (spec table, §5.3 #4):

    flight_pairs == 2  →  at least 1 on A and 2 on D
    flight_pairs == 1  →  at least 1 on A and 1 on D
    flight_pairs == 0  →  no flight-shift minimum that day

This is a FLOOR, not an exact target (manual roster WR JUN26 + spec §6): every
person on duty that day is on a real flight shift (A / D / A/D), not just the
bare minimum — extra A/D coverage above the floor is fine and expected. The
even split between A and D is shaped by the balance objective, not capped here.
O/D is no longer auto-assigned, so a working day is always A, D or A/D.

An ``A/D`` assignment covers one A AND one D simultaneously (§5.3 #6 — the
last-resort double shift; discouraged via a moderate objective penalty). Only
UNDER-coverage is penalized (a Violation suggesting the A/D fallback, §5.6 #13);
there is no upper bound on a shift's headcount.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.slack_registry import SlackRegistry

# Minimum demand_A, demand_D per flight_pairs value (§5.3 #4).
DEMAND: dict[int, tuple[int, int]] = {0: (0, 0), 1: (1, 1), 2: (1, 2)}


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    if not inp.people:
        return

    for d in sorted(inp.days):
        pairs = inp.flight_pairs.get(d, 0)
        demand_a, demand_d = DEMAND.get(pairs, (0, 0))
        if demand_a == 0 and demand_d == 0:
            continue  # no flight ops that day → no minimum to enforce

        # Everyone on duty takes a flight shift, so count across all people.
        sum_a = sum(x[(p.user_id, d, AttendanceCode.A)] for p in inp.people)
        sum_d = sum(x[(p.user_id, d, AttendanceCode.D)] for p in inp.people)
        sum_ad = sum(x[(p.user_id, d, AttendanceCode.A_D)] for p in inp.people)

        for shift, total, demand in (("A", sum_a, demand_a), ("D", sum_d, demand_d)):
            label = f"staff_{shift}_{d.isoformat()}"
            # Floor only: total + A/D + under >= demand (no over cap).
            under = model.NewIntVar(0, len(inp.people), f"{label}_under")
            # A/D covers one unit of BOTH shifts (§5.3 #6).
            model.Add(total + sum_ad + under >= demand)

            registry.register(
                under,
                rule="flight_staffing",
                message=(
                    f"{d}: short {shift}-shift coverage (need at least {demand}); "
                    f"consider an A/D double shift (§5.3 #6) or a manual edit (F-09)"
                ),
                day=d,
            )
