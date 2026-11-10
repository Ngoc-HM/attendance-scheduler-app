"""Counts of items waiting for an admin decision (owner 2026-11-10).

Feeds the numbers next to the admin's navigation tabs. COUNT queries only —
no rows are loaded. "Waiting for the admin" is ``pending`` for every kind:
leave requests (monthly + annual), shift-change / swap requests (there is no
colleague acceptance step, the admin decides them directly) and
self-registered accounts.
"""

from __future__ import annotations

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.models.enums import LeaveStatus, UserStatus
from app.models.leave import LeaveRequest
from app.models.shift_change_request import ShiftChangeRequest
from app.models.user import User
from app.schemas.pending_counts import PendingCounts


def _count(db: Session, model: type, condition: ColumnElement[bool]) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(condition)) or 0)


def get_counts(db: Session) -> PendingCounts:
    return PendingCounts(
        leaves=_count(
            db, LeaveRequest, LeaveRequest.status == LeaveStatus.pending
        ),
        shift_changes=_count(
            db, ShiftChangeRequest, ShiftChangeRequest.status == LeaveStatus.pending
        ),
        users=_count(db, User, User.status == UserStatus.pending),
    )
