"""Admin dashboard endpoint (customer 2026-11-18)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.dashboard import DashboardRead
from app.services import dashboard_service

router = APIRouter()


@router.get("", response_model=DashboardRead)
def dashboard(db: DbSession, _admin: AdminUser):
    """Today's duty, missing punches, waiting requests, roster state, leave."""
    return dashboard_service.overview(db)
