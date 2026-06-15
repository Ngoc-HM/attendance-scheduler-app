"""Automatic calculations (F-14 — comp days / carry-over)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.services import calculation_service

router = APIRouter()


@router.post("/{year}/{month}/close")
def close_month(db: DbSession, year: int, month: int, _admin: AdminUser):
    """F-14 — close a month: recompute carry_comp / carry_streak /
    carry_premium_off for the next month (§5.5, §5.3 #6, decision #6).

    Idempotent: values are absolute recomputations from the record history.
    """
    return calculation_service.close_month(db, year, month)


@router.get("/summary")
def carry_summary(db: DbSession, _admin: AdminUser):
    """Current per-user carry values (comp / streak / premium-off / AL balance)."""
    return calculation_service.summary(db)
