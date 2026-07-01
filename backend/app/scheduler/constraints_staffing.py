"""§5.3 #4 + #6 — daily flight-shift staffing from flight pairs (soft floor).

Scoped to ROLE-A people only (owner decision 2026-06-26): only the fixed group
takes A / D / A/D flight duties.  Role T (AD) and role M (O/D) are never
counted toward flight-pair coverage.

Per-day MINIMUM coverage required (spec table, §5.3 #4):

    flight_pairs == 2  →  at least 1 on A and 2 on D
    flight_pairs == 1  →  at least 1 on A and 1 on D
    flight_pairs == 0  →  no flight-shift minimum that day

This is a FLOOR, not an exact target: extra coverage above the floor is fine.
An ``A/D`` assignment covers one A AND one D simultaneously (§5.3 #6 — the
last-resort double shift; discouraged via a moderate objective penalty). Only
UNDER-coverage is penalized (a Violation suggesting the A/D fallback, §5.6 #13);
there is no upper bound on a shift's headcount.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
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
    # Only role-A people have A / D / A/D vars.
    role_a = [p for p in inp.people if p.role is Role.A]
    if not role_a:
        return

    for d in sorted(inp.days):
        pairs = inp.flight_pairs.get(d, 0)
        demand_a, demand_d = DEMAND.get(pairs, (0, 0))
        if demand_a == 0 and demand_d == 0:
            continue  # no flight ops that day → no minimum to enforce

        # Count A / D / A/D across role-A people only.
        sum_a = sum(x[(p.user_id, d, AttendanceCode.A)] for p in role_a)
        sum_d = sum(x[(p.user_id, d, AttendanceCode.D)] for p in role_a)
        sum_ad = sum(x[(p.user_id, d, AttendanceCode.A_D)] for p in role_a)

        for shift, total, demand in (("A", sum_a, demand_a), ("D", sum_d, demand_d)):
            label = f"staff_{shift}_{d.isoformat()}"
            # Floor only: total + A/D + under >= demand (no over cap).
            under = model.NewIntVar(0, len(role_a), f"{label}_under")
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
