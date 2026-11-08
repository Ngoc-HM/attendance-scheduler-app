"""Shared schema building blocks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# Accepted calendar years for any year/month input (same range as
# GenerateScheduleRequest): out-of-range values answer 422, never a 500.
YEAR_MIN = 2000
YEAR_MAX = 2100


class ORMModel(BaseModel):
    """Base for response models read from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    detail: str
