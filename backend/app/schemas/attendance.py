"""Attendance & holiday schemas (F-11, F-12, F-13)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.models.enums import AttendanceCode
from app.schemas.common import ORMModel


class AttendanceUpsert(BaseModel):
    user_id: int
    work_date: date
    code: AttendanceCode
    note: str | None = None


class AttendanceRead(ORMModel):
    id: int
    user_id: int
    work_date: date
    code: AttendanceCode
    recorded_by: int | None
    note: str | None


class HolidayUpsert(BaseModel):
    day: date
    name: str


class HolidayRead(ORMModel):
    id: int
    day: date
    name: str
