"""Auto comp-day off — force every person to use up last month's comp debt.

Customer decision 2026-06-12 (hướng B): a person who worked an A/D double
shift earns a comp day (CD, §5.3 #6). Owner decision D1 (2026-11-06): anyone,
of any role, who works on a public holiday also earns one CD. The following
month the system itself schedules those owed CD rest days — the person does
NOT register them.

Modeled as a SOFT rule so it never makes the model infeasible and, crucially,
**yields to flight staffing**: the comp slack carries a lower weight than the
staffing slack, so when granting a CD would leave a flight short the solver
drops the CD and reports a ``comp_day_shortfall`` Violation instead (§5.6).

Per person (every role) with ``carry_comp = c``:

    sum(CD over the month) + under - over == c        (c > 0, soft)
    sum(CD over the month) == 0                        (c == 0, hard)

``under`` = owed comp days the schedule could not grant (the meaningful
shortfall); ``over`` guards against the solver handing out unearned CD rest.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.slack_registry import SlackRegistry

# Below staffing slack (10_000 → CD yields to flights) but above every soft
# objective (max 1_000 → CD is granted rather than skipped for prettier balance).
COMP_WEIGHT = 2_000


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    days = sorted(inp.days)
    # CD is in every role's domain (role_codes), so the rule covers everyone.
    for p in inp.people:
        cd_sum = sum(x[(p.user_id, d, AttendanceCode.CD)] for d in days)
        owed = p.carry_comp

        if owed <= 0:
            # No comp debt → never auto-assign CD (CD comes only from debt).
            model.add(cd_sum == 0)
            continue

        under = model.new_int_var(0, owed, f"comp_under_{p.user_id}")
        over = model.new_int_var(0, len(days), f"comp_over_{p.user_id}")
        model.add(cd_sum + under - over == owed)

        registry.register(
            under,
            rule="comp_day_shortfall",
            message=(
                f"User {p.user_id}: {owed} comp day(s) owed but the schedule "
                f"could not grant all of them this month"
            ),
            user_id=p.user_id,
            weight=COMP_WEIGHT,
        )
        registry.register(
            over,
            rule="comp_day_excess",
            message=(
                f"User {p.user_id}: more comp days scheduled than the "
                f"{owed} owed"
            ),
            user_id=p.user_id,
            weight=COMP_WEIGHT,
        )
