"""Public holiday logic (F-13).

Holidays are NORMAL WORKING DAYS (locked decision #5) — these rows are only
"premium-off markers": being OFF on one is a perk balanced across months
(decision #6). They are never auto-pinned off. ``holiday_dates`` feeds the
scheduler's premium-off objective; ``schedule_input_builder`` has its own
month-scoped reader for the same table.
"""

from __future__ import annotations

import calendar
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.holiday import Holiday
from app.schemas.attendance import HolidayUpsert


def list_year(db: Session, year: int) -> list[Holiday]:
    first, last = date(year, 1, 1), date(year, 12, 31)
    return (
        db.query(Holiday)
        .filter(Holiday.day >= first, Holiday.day <= last)
        .order_by(Holiday.day)
        .all()
    )


def upsert(db: Session, payload: HolidayUpsert) -> Holiday:
    """Create or rename a holiday (unique by ``day``)."""
    holiday = db.query(Holiday).filter(Holiday.day == payload.day).one_or_none()
    if holiday is None:
        holiday = Holiday(day=payload.day, name=payload.name)
        db.add(holiday)
    else:
        holiday.name = payload.name
    db.commit()
    db.refresh(holiday)
    return holiday


def delete(db: Session, holiday_id: int) -> None:
    holiday = db.get(Holiday, holiday_id)
    if holiday is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("holiday.not_found"))
    db.delete(holiday)
    db.commit()


def holiday_dates(db: Session, year: int, month: int) -> set[date]:
    """Holidays within (year, month) — premium-off markers for the scheduler."""
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    rows = db.query(Holiday).filter(Holiday.day >= first, Holiday.day <= last).all()
    return {h.day for h in rows}
