"""§5.3 #4 + #6 — fixed-group (A1–A4) daily staffing from flight pairs (soft).

Demand per day, covered by the FIXED group only (spec table, §5.3 #4):

    flight_pairs == 2  →  1 on A and 2 on D
    flight_pairs == 1  →  1 on A and 1 on D
    flight_pairs == 0  →  no flight-shift staffing (and none allowed)

An ``A/D`` assignment covers one A AND one D simultaneously (§5.3 #6 — the
last-resort double shift; its usage is discouraged via a moderate objective
penalty in ``objectives``, and it earns +1 workday / 1 CD handled by F-14).

Modeled as equalities with under/over slack so the model stays feasible:
``sum(A) + sum(A/D) + under - over == demand``. Under-coverage reports a
Violation that suggests the A/D fallback (§5.6 #13).
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.slack_registry import SlackRegistry

# demand_A, demand_D per flight_pairs value (§5.3 #4).
DEMAND: dict[int, tuple[int, int]] = {0: (0, 0), 1: (1, 1), 2: (1, 2)}


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    fixed = [p for p in inp.people if p.role.is_fixed]
    if not fixed:
        return  # nothing to staff (e.g. unit tests with only flexible roles)

    for d in sorted(inp.days):
        pairs = inp.flight_pairs.get(d, 0)
        demand_a, demand_d = DEMAND.get(pairs, (0, 0))

        sum_a = sum(x[(p.user_id, d, AttendanceCode.A)] for p in fixed)
        sum_d = sum(x[(p.user_id, d, AttendanceCode.D)] for p in fixed)
        sum_ad = sum(x[(p.user_id, d, AttendanceCode.A_D)] for p in fixed)

        for shift, total, demand in (("A", sum_a, demand_a), ("D", sum_d, demand_d)):
            label = f"staff_{shift}_{d.isoformat()}"
            under = model.NewIntVar(0, 4, f"{label}_under")
            over = model.NewIntVar(0, 4, f"{label}_over")
            # A/D covers one unit of BOTH shifts (§5.3 #6).
            model.Add(total + sum_ad + under - over == demand)

            registry.register(
                under,
                rule="fixed_group_staffing",
                message=(
                    f"{d}: short {shift}-shift coverage in the fixed group "
                    f"(need {demand}); consider an A/D double shift (§5.3 #6) "
                    f"or a manual edit (F-09)"
                ),
                day=d,
            )
            registry.register(
                over,
                rule="fixed_group_staffing",
                message=(
                    f"{d}: more {shift}-shift assignments than the demand "
                    f"of {demand} for the fixed group"
                ),
                day=d,
            )
