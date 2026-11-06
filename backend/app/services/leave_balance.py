"""Annual leave quota and remaining balance (owner decision D4, 2026-11-06).

Each user carries an admin-set ``annual_leave_quota`` (days per calendar
year). No per-year balance is stored: it is derived from the leave requests,
so approving, rejecting or revoking shows up immediately.

- annual_leave_summary: quota, used (approved), pending and remaining days of
  one person in one calendar year.
- exceeds_quota: whether approving a pending request takes its owner past the
  quota in any year it touches (an advisory warning; the admin decides).
"""

from __future__ import annotations

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.i18n import t
from app.models.enums import LeaveStatus
from app.models.leave import LeaveRequest
from app.models.user import User
from app.schemas.leave import AnnualLeaveSummary


def _days_in_year(req: LeaveRequest, year: int) -> int:
    """Calendar days of ``req`` that fall inside ``year`` (0 when none)."""
    start = max(req.start_date, date(year, 1, 1))
    end = min(req.end_date, date(year, 12, 31))
    return max((end - start).days + 1, 0)


def annual_leave_summary(db: Session, user_id: int, year: int) -> AnnualLeaveSummary:
    """Quota, approved (``used``) and pending leave days of ``user_id`` in
    ``year``; a request crossing New Year counts only its days in ``year``.
    """
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("user.not_found"))

    requests = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.user_id == user_id,
            LeaveRequest.status.in_([LeaveStatus.approved, LeaveStatus.pending]),
            LeaveRequest.start_date <= date(year, 12, 31),
            LeaveRequest.end_date >= date(year, 1, 1),
        )
        .all()
    )
    used = sum(
        _days_in_year(r, year) for r in requests if r.status == LeaveStatus.approved
    )
    pending = sum(
        _days_in_year(r, year) for r in requests if r.status == LeaveStatus.pending
    )
    return AnnualLeaveSummary(
        year=year,
        quota=user.annual_leave_quota,
        used=used,
        pending=pending,
        remaining=user.annual_leave_quota - used,
    )


def exceeds_quota(db: Session, req: LeaveRequest) -> bool:
    """True when approving the still-pending ``req`` would leave its owner
    with a negative remaining balance in any calendar year it touches."""
    return any(
        annual_leave_summary(db, req.user_id, year).remaining
        - _days_in_year(req, year)
        < 0
        for year in range(req.start_date.year, req.end_date.year + 1)
    )
