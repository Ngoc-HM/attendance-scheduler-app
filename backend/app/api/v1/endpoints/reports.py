"""Reporting & export endpoints (F-15).

The service returns a neutral ``ReportTable``; ``?format=csv|xlsx`` selects the
serializer (new formats need no API change, spec §4.7). Admin-only for now;
non-admin own-data + S-masking lands in phase 10.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.deps import AdminUser, DbSession
from app.api.params import MonthPath, YearPath
from app.services import audit_service, report_serializers, report_service, roster_report
from app.services.roster_xlsx import build_workbook, file_name

router = APIRouter()


def _stream(table, fmt: str, filename: str) -> StreamingResponse:
    fmt = fmt if fmt in report_serializers.CONTENT_TYPES else "csv"
    media_type, ext = report_serializers.CONTENT_TYPES[fmt]
    data = report_serializers.serialize(table, fmt)
    return StreamingResponse(
        iter([data]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}.{ext}"'},
    )


@router.get("/monthly/{year}/{month}")
def monthly_report(
    db: DbSession, year: YearPath, month: MonthPath, admin: AdminUser,
    format: str = Query("csv"),
):
    """F-15 — attendance export for a single month."""
    table = report_service.monthly(db, year, month)
    audit_service.record(db, admin.id, "report.export", "Report",
                         detail=f"monthly {year}-{month:02d} {format}")
    return _stream(table, format, f"attendance_{year}_{month:02d}")


@router.get("/yearly/{year}")
def yearly_report(
    db: DbSession, year: YearPath, admin: AdminUser, format: str = Query("csv")
):
    """F-15 — attendance export for a full year."""
    table = report_service.yearly(db, year)
    audit_service.record(db, admin.id, "report.export", "Report",
                         detail=f"yearly {year} {format}")
    return _stream(table, format, f"attendance_{year}")


@router.get("/leave-balance/{year}")
def leave_balance_report(
    db: DbSession, year: YearPath, admin: AdminUser, format: str = Query("csv")
):
    """Leave quota, approved, pending and remaining days of everyone in a year."""
    table = report_service.leave_balance_report(db, year)
    audit_service.record(db, admin.id, "report.export", "Report",
                         detail=f"leave {year} {format}")
    return _stream(table, format, f"leave_{year}")


@router.get("/roster/{year}/{month}")
def roster_report_wr(db: DbSession, year: YearPath, month: MonthPath, admin: AdminUser):
    """The month's roster in the customer's workbook layout (decision #70):
    always .xlsx, people by code only; 404 when the month has no roster."""
    data = build_workbook(roster_report.build(db, year, month, admin))
    audit_service.record(db, admin.id, "report.export", "Report",
                         detail=f"roster {year}-{month:02d} xlsx")
    media_type, _ = report_serializers.CONTENT_TYPES["xlsx"]
    return StreamingResponse(
        iter([data]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name(year, month)}"'},
    )
