"""§5.3 #4 — daily flight-shift staffing from flight pairs (soft floor).

Scoped to ROLE-A people only (owner decision 2026-06-26): only the fixed group
takes A or D flight duties. Role T/F (AD) and role M (O/D) are never counted
toward flight-pair coverage.

Per-day MINIMUM coverage required (spec table, §5.3 #4):

    flight_pairs == 2  →  at least 1 on A and 2 on D
    flight_pairs == 1  →  at least 1 on A and 1 on D
    flight_pairs == 0  →  no flight-shift minimum that day

This is a FLOOR, not an exact target: extra coverage above the floor is fine.
The automatic solver never creates A/D. Under-coverage is returned as a
Violation; A/D can only be recorded later for a real unexpected absence.

The shortfall of a shift is bounded by its demand, not by the role-A head
count: with the only role-A person on leave on a 2-pair day the D shortfall is
2. With no role-A people at all, every flight day is one fixed shortfall,
reported once per day like ``schedule_violation_checker.check_staffing``.
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
    # Only role-A people have A / D vars.
    role_a = [p for p in inp.people if p.role is Role.A]

    for d in sorted(inp.days):
        pairs = inp.flight_pairs.get(d, 0)
        demand_a, demand_d = DEMAND.get(pairs, (0, 0))
        if demand_a == 0 and demand_d == 0:
            continue  # no flight ops that day → no minimum to enforce

        if not role_a:
            # Nobody can cover: the whole demand is short (a constant slack).
            registry.register(
                model.new_constant(demand_a + demand_d),
                rule="flight_staffing",
                message=(
                    f"{d}: no role-A staff for flight coverage (need at least "
                    f"{demand_a} on A and {demand_d} on D)"
                ),
                day=d,
                key="flight_staffing_no_role_a",
                params={"need_a": demand_a, "need_d": demand_d},
            )
            continue

        # Count A and D across role-A people only.
        sum_a = sum(x[(p.user_id, d, AttendanceCode.A)] for p in role_a)
        sum_d = sum(x[(p.user_id, d, AttendanceCode.D)] for p in role_a)

        for shift, total, demand in (("A", sum_a, demand_a), ("D", sum_d, demand_d)):
            label = f"staff_{shift}_{d.isoformat()}"
            # Floor only: total + under >= demand (no over cap). ``under`` can
            # reach the whole demand (everyone on leave), never more.
            under = model.new_int_var(0, demand, f"{label}_under")
            model.add(total + under >= demand)

            registry.register(
                under,
                rule="flight_staffing",
                message=(
                    f"{d}: short {shift}-shift coverage (need at least {demand}); "
                    "automatic scheduling will not assign an A/D double shift"
                ),
                day=d,
                params={"shift": shift, "need": demand},
            )
