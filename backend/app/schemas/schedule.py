"""Schedule schemas (F-07, F-08, F-09)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import AttendanceCode, ScheduleStatus
from app.schemas.common import ORMModel


class GenerateScheduleRequest(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    # Overrides the published/manual-edit regenerate guards (admin intent).
    force: bool = False


class ShiftAssignmentRead(ORMModel):
    id: int
    user_id: int
    work_date: date
    code: AttendanceCode
    is_manual_override: bool
    # Planned by the previous month's generation (owner 2026-11-18).
    carried: bool = False


class ManualOverrideRequest(BaseModel):
    """Admin manual edit after auto-generation (F-09)."""

    user_id: int
    work_date: date
    code: AttendanceCode


class ConstraintViolation(BaseModel):
    """A hard-constraint violation surfaced to the admin (§5.6)."""

    day: date | None = None
    user_id: int | None = None
    rule: str
    message: str


class MonthlyScheduleRead(ORMModel):
    id: int
    year: int
    month: int
    status: ScheduleStatus
    generated_at: datetime | None
    note: str | None
    assignments: list[ShiftAssignmentRead] = []
    # The next month's carried cells this month's generation planned (its
    # days up to the Sunday ending this month's last week).
    carry_assignments: list[ShiftAssignmentRead] = []


class ScheduleResult(BaseModel):
    """Outcome of a solver run (§5.2, §5.6)."""

    feasible: bool
    schedule: MonthlyScheduleRead | None = None
    violations: list[ConstraintViolation] = []
    # Generate only: rule breaches the new roster CREATES in the following
    # month when that month already has a schedule ("YYYY-MM: message") —
    # weeks and runs cross the month boundary (owner 2026-11-13).
    next_month_warnings: list[str] = []
    # Generate only: things the admin should follow up that are not rule
    # breaches — e.g. the next month's flights are not entered, so the days
    # this roster runs into took their flight count by weekday.
    notices: list[str] = []
    # Present for generated schedules; manual edits do not run the solver.
    solver_status: str | None = None
    slack_proven_minimal: bool = False
    phase_diagnostics: list[dict[str, object]] = Field(default_factory=list)
