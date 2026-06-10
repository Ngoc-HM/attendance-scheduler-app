"""Reporting & export endpoints (F-15).

Export layout is intentionally flexible (spec §4.7 [CHỐT]): the service
returns structured rows that an exporter renders to Excel/CSV/etc., so new
formats can be added without touching the API.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession

router = APIRouter()


@router.get("/monthly/{year}/{month}")
def monthly_report(db: DbSession, year: int, month: int):
    """F-15 — attendance export for a single month."""
    # TODO: delegate to report_service.monthly(db, year, month)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.get("/yearly/{year}")
def yearly_report(db: DbSession, year: int):
    """F-15 — attendance export for a full year."""
    # TODO: delegate to report_service.yearly(db, year)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
