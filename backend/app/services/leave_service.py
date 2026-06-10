"""Leave logic (F-05, F-06) and conflict-priority helpers (§5.4 #9)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.enums import LeaveStatus
from app.models.leave import LeaveRequest
from app.schemas.leave import LeaveCreate


def list_for_user(db: Session, user_id: int) -> list[LeaveRequest]:
    raise NotImplementedError  # TODO


def create(db: Session, user_id: int, payload: LeaveCreate) -> LeaveRequest:
    """F-05/F-06 — register leave.

    Validate the registration window (monthly close on the 20th; annual leave
    of >= 5 consecutive days uses the annual bucket).
    """
    raise NotImplementedError  # TODO


def list_pending(db: Session) -> list[LeaveRequest]:
    raise NotImplementedError  # TODO


def decide(db: Session, leave_id: int, status: LeaveStatus) -> LeaveRequest:
    """Admin approve/reject. On conflicts, apply priority order (§5.4 #9):
    (a) larger ``carry_comp`` first, (b) guarantee 2 days off/week,
    (c) prefer weekend pairing."""
    raise NotImplementedError  # TODO
