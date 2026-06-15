"""Reporting & export endpoints (F-15).

The service returns a neutral ``ReportTable``; ``?format=csv|xlsx`` selects the
serializer (new formats need no API change, spec §4.7). Admin-only for now;
non-admin own-data + S-masking lands in phase 10.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.deps import AdminUser, DbSession
from app.services import audit_service, report_serializers, report_service

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
    db: DbSession, year: int, month: int, admin: AdminUser,
    format: str = Query("csv"),
):
    """F-15 — attendance export for a single month."""
    table = report_service.monthly(db, year, month)
    audit_service.record(db, admin.id, "report.export", "Report",
                         detail=f"monthly {year}-{month:02d} {format}")
    return _stream(table, format, f"attendance_{year}_{month:02d}")


@router.get("/yearly/{year}")
def yearly_report(
    db: DbSession, year: int, admin: AdminUser, format: str = Query("csv")
):
    """F-15 — attendance export for a full year."""
    table = report_service.yearly(db, year)
    audit_service.record(db, admin.id, "report.export", "Report",
                         detail=f"yearly {year} {format}")
    return _stream(table, format, f"attendance_{year}")
