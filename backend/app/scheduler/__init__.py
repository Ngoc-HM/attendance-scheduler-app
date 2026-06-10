"""Constraint-solver scheduling engine (spec §5).

Public surface:
    SolverInput / SolverOutput  – data in/out (``domain``)
    SchedulerEngine             – builds & solves the CP-SAT model (``engine``)

Hard constraints live in ``constraints`` (§5.3), soft objectives in
``objectives`` (§5.4), and calendar helpers (week partition §5.1, consecutive
streak §5.5) in ``calendar_utils``.
"""

from app.scheduler.domain import (
    AssignmentResult,
    PersonInput,
    SolverInput,
    SolverOutput,
    Violation,
)
from app.scheduler.engine import SchedulerEngine

__all__ = [
    "AssignmentResult",
    "PersonInput",
    "SchedulerEngine",
    "SolverInput",
    "SolverOutput",
    "Violation",
]
