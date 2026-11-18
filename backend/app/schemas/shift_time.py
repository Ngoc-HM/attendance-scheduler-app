"""Shift time-frame DTOs (decision #71). Times travel as ``HH:MM`` text."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ShiftTimeRead(BaseModel):
    """One shift's frame. ``derived`` marks the double shift (A/D), computed
    from A and D and never editable."""

    code: str
    start: str
    end: str
    derived: bool = False


class ShiftTimeWrite(BaseModel):
    code: Literal["A", "D"]
    # "HH:MM"; the service checks the format and that start < end, so the
    # message is translated.
    start: str = Field(max_length=5)
    end: str = Field(max_length=5)


class ShiftTimesUpdate(BaseModel):
    frames: list[ShiftTimeWrite] = Field(min_length=1, max_length=2)


class ShiftToday(BaseModel):
    """The signed-in person's code today and its frame (null when the code
    has no shift frame, or there is no code)."""

    code: str | None = None
    start: str | None = None
    end: str | None = None
