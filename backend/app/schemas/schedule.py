"""Schedule schemas (F-07, F-08, F-09)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import AttendanceCode, ScheduleStatus
from app.schemas.common import ORMModel


class GenerateScheduleRequest(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)


class ShiftAssignmentRead(ORMModel):
    id: int
    user_id: int
    work_date: date
    code: AttendanceCode
    is_manual_override: bool


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


class ScheduleResult(BaseModel):
    """Outcome of a solver run (§5.2, §5.6)."""

    feasible: bool
    schedule: MonthlyScheduleRead | None = None
    violations: list[ConstraintViolation] = []
