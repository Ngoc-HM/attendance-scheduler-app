"""Public holiday logic (F-13)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.holiday import Holiday
from app.schemas.attendance import HolidayUpsert


def list_year(db: Session, year: int) -> list[Holiday]:
    raise NotImplementedError  # TODO


def upsert(db: Session, payload: HolidayUpsert) -> Holiday:
    raise NotImplementedError  # TODO


def delete(db: Session, holiday_id: int) -> None:
    raise NotImplementedError  # TODO
