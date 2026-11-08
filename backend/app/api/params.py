"""Bounded year/month request parameters (review 2026-11-08, section E).

An unchecked ``month=13`` or ``year=0`` reaches ``date()`` / ``calendar`` and
crashes with a 500; these aliases make FastAPI answer 422 instead. The year
range matches ``GenerateScheduleRequest`` (2000..2100).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Path, Query

from app.schemas.common import YEAR_MAX, YEAR_MIN

__all__ = ["YEAR_MAX", "YEAR_MIN", "MonthPath", "MonthQuery", "YearPath", "YearQuery"]

YearQuery = Annotated[int, Query(ge=YEAR_MIN, le=YEAR_MAX)]
MonthQuery = Annotated[int, Query(ge=1, le=12)]
YearPath = Annotated[int, Path(ge=YEAR_MIN, le=YEAR_MAX)]
MonthPath = Annotated[int, Path(ge=1, le=12)]
