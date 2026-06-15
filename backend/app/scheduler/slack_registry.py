"""Slack-variable registry — the always-feasible architecture (decision #2).

Staffing and off-day rules are modeled as SOFT constraints: each gets a slack
variable with a very large penalty, so the CP-SAT model always has a solution.
After solving, any slack > 0 is translated into a ``Violation`` (§5.6 #12–14)
that tells the admin exactly which rule broke, where, and for whom — instead
of an opaque "infeasible".

Only "exactly one status per cell" and the approved-off pins stay truly hard.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ortools.sat.python import cp_model

from app.scheduler.domain import Violation

# Penalty applied to every slack unit. Must dwarf the sum of all soft
# objective weights so the solver only "buys" slack when genuinely forced.
SLACK_WEIGHT = 10_000


@dataclass(frozen=True)
class SlackEntry:
    """One registered slack variable plus the violation metadata it implies."""

    var: cp_model.IntVar
    rule: str
    message: str
    day: date | None = None
    user_id: int | None = None
    weight: int = SLACK_WEIGHT


class SlackRegistry:
    """Collects slack vars during model build; reports violations after solve."""

    def __init__(self) -> None:
        self._entries: list[SlackEntry] = []

    def register(
        self,
        var: cp_model.IntVar,
        rule: str,
        message: str,
        day: date | None = None,
        user_id: int | None = None,
        weight: int = SLACK_WEIGHT,
    ) -> None:
        # Lower-weight slack lets a rule yield to higher-weight ones (e.g. the
        # auto comp-day rule yields to flight staffing — customer 2026-06-12).
        self._entries.append(SlackEntry(var, rule, message, day, user_id, weight))

    def penalty_terms(self) -> list[cp_model.LinearExpr]:
        """Weighted slack terms for the objective (minimized)."""
        return [e.weight * e.var for e in self._entries]

    def violations(self, solver: cp_model.CpSolver) -> list[Violation]:
        """Translate every slack > 0 into an admin-facing Violation (§5.6)."""
        found: list[Violation] = []
        for e in self._entries:
            value = solver.Value(e.var)
            if value > 0:
                found.append(
                    Violation(
                        rule=e.rule,
                        message=f"{e.message} (shortfall: {value})",
                        day=e.day,
                        user_id=e.user_id,
                    )
                )
        return found
