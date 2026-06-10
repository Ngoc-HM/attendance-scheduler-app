"""Automatic calculations (F-14 — overtime / carry-over comp days)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AdminUser, DbSession

router = APIRouter()


@router.post("/{year}/{month}/close")
def close_month(db: DbSession, year: int, month: int, _admin: AdminUser):
    """F-14 — close a month: compute comp days (CD) and carry-over values
    (``carry_comp`` / ``carry_streak``, §5.5) into the next month.

    Per F-14, only the current comp-day logic is handled — no complex annual
    leave accrual.
    """
    # TODO: delegate to calculation_service.close_month(db, year, month)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
