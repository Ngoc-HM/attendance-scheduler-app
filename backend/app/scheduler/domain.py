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
    # Premium OFF days (off on Sat/Sun/holiday) received so far — balanced
    # across months by the premium-off fairness objective (decision #6).
    carry_premium_off: int = 0


@dataclass(frozen=True)
class SolverInput:
    year: int
    month: int
    people: list[PersonInput]
    days: list[date]                       # every day of the month (§5.1)
    weeks: list[list[date]]                # partition of ``days`` into weeks (§5.1)
    flight_pairs: dict[date, int]          # flightPairs[d] ∈ {0,1,2} (§5.3 #4)
    # Pre-pinned off cells: approved leave (AL/CD) (§5.3 #5). Holidays are NOT
    # pinned off — they are normal working days (decision #5).
    approved_off: dict[int, dict[date, AttendanceCode]] = field(default_factory=dict)
    # Public holidays: working days, but an OFF landing on one is "premium"
    # (like Sat/Sun) and feeds the premium-off fairness objective (decision #6).
    holidays: set[date] = field(default_factory=set)
    # Approved ANNUAL-leave days per user — exempt from the "no more than 5
    # consecutive OFF days" rule (annual leave IS the sanctioned long break;
    # customer clarification 2026-06-12).
    long_leave_off: dict[int, set[date]] = field(default_factory=dict)
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
