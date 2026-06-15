"""Pluggable serializers for ``ReportTable`` (F-15) — CSV + XLSX.

Adding a new export format = adding one ``to_*`` function here; the data
assembly (``report_table``) never changes (spec §4.7 flexible layout).
"""

from __future__ import annotations

import csv
import io

from openpyxl import Workbook

from app.services.report_table import ReportTable

# (media type, file extension) per format key.
CONTENT_TYPES = {
    "csv": ("text/csv", "csv"),
    "xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
    ),
}


def serialize(table: ReportTable, fmt: str) -> bytes:
    if fmt == "xlsx":
        return to_xlsx(table)
    return to_csv(table)


def to_csv(table: ReportTable) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(table.headers)
    writer.writerows(table.rows)
    return buf.getvalue().encode("utf-8-sig")  # BOM → Excel opens UTF-8 cleanly


def to_xlsx(table: ReportTable) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = table.title[:31]  # Excel sheet-name limit
    ws.append(table.headers)
    for row in table.rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
