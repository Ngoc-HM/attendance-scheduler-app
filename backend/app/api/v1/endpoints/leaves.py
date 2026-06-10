"""Leave registration endpoints (F-05, F-06)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ActiveUser, AdminUser, DbSession
from app.schemas.leave import LeaveCreate, LeaveDecision, LeaveRead

router = APIRouter()


@router.get("/mine", response_model=list[LeaveRead])
def my_leaves(db: DbSession, current_user: ActiveUser):
    # TODO: delegate to leave_service.list_for_user(db, current_user.id)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("", response_model=LeaveRead, status_code=status.HTTP_201_CREATED)
def request_leave(db: DbSession, payload: LeaveCreate, current_user: ActiveUser):
    """F-05/F-06 — register leave (monthly < 5 days, or annual >= 5 days)."""
    # TODO: delegate to leave_service.create(db, current_user.id, payload)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.get("/pending", response_model=list[LeaveRead])
def pending_leaves(db: DbSession, _admin: AdminUser):
    # TODO: delegate to leave_service.list_pending(db)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")


@router.post("/{leave_id}/decision", response_model=LeaveRead)
def decide_leave(db: DbSession, leave_id: int, payload: LeaveDecision, _admin: AdminUser):
    """Admin approves/rejects a leave request (spec §3, §5.4 #9)."""
    # TODO: delegate to leave_service.decide(db, leave_id, payload.status)
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Not implemented yet")
