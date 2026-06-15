"""Reporting / export logic (F-15).

Assembles a neutral ``ReportTable`` from ACTUAL attendance records; the
endpoint renders it via ``report_serializers`` (CSV/XLSX). Data and format are
separate so new layouts need no API change (spec §4.7).
"""

from __future__ import annotations

from app.models.user import User
from app.scheduler.calendar_utils import month_days
from app.services import attendance_service
from app.services.report_table import ReportTable, UserRow, build_monthly, build_yearly


def _user_rows(db) -> list[UserRow]:
    users = db.query(User).order_by(User.id).all()
    return [UserRow(user_id=u.id, name=u.full_name, role=u.role.value) for u in users]


def monthly(db, year: int, month: int) -> ReportTable:
    """F-15 — person × day matrix + per-person totals for one month."""
    return build_monthly(
        users=_user_rows(db),
        days=month_days(year, month),
        grid=attendance_service.actual_records_map(db, year, month),
    )


def yearly(db, year: int) -> ReportTable:
    """F-15 — person × month working-day totals for a full year."""
    grids = {
        m: attendance_service.actual_records_map(db, year, m) for m in range(1, 13)
    }
    return build_yearly(users=_user_rows(db), year=year, grids_by_month=grids)
