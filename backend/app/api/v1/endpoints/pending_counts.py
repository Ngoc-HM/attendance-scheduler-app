"""Admin navigation badge counts (owner 2026-11-10). Read-only: no audit."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.pending_counts import PendingCounts
from app.services import pending_counts_service

router = APIRouter()


@router.get("", response_model=PendingCounts)
def get_pending_counts(db: DbSession, _admin: AdminUser) -> PendingCounts:
    """How many leaves, shift changes and accounts wait for an admin decision."""
    return pending_counts_service.get_counts(db)
