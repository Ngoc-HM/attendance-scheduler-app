"""Solver input/output data structures (spec §5.1 / §5.2).

Plain dataclasses so the engine is decoupled from the database/ORM. The
service layer (``schedule_service``) maps ORM rows into ``SolverInput`` and
persists ``SolverOutput``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.models.enums import AttendanceCode, Role


@dataclass(frozen=True)
class PersonInput:
    user_id: int
    role: Role
    # Carry-over from the previous month (§5.1).
    carry_comp: int = 0     # outstanding comp days → conflict tie-breaker (§5.4 #9)
    carry_streak: int = 0   # consecutive working days at month start (§5.5)


@dataclass(frozen=True)
class SolverInput:
    year: int
    month: int
    people: list[PersonInput]
    days: list[date]                       # every day of the month (§5.1)
    weeks: list[list[date]]                # partition of ``days`` into weeks (§5.1)
    flight_pairs: dict[date, int]          # flightPairs[d] ∈ {0,1,2} (§5.3 #4)
    # Pre-pinned off cells: approved leave (AL/CD) and holidays (X) (§5.3 #5).
    approved_off: dict[int, dict[date, AttendanceCode]] = field(default_factory=dict)
    max_solve_seconds: float = 30.0


@dataclass
class AssignmentResult:
    user_id: int
    day: date
    code: AttendanceCode


@dataclass
class Violation:
    """A hard-constraint breach reported back to the admin (§5.6)."""

    rule: str
    message: str
    day: date | None = None
    user_id: int | None = None


@dataclass
class SolverOutput:
    feasible: bool
    assignments: list[AssignmentResult] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)
