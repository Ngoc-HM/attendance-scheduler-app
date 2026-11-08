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

# Ruling R7 (B1): a cell starting with one of these is run as a formula by
# Excel/LibreOffice (CSV injection, e.g. a self-registered name
# ``=HYPERLINK(...)``). Prefixing ``'`` keeps the text but makes it inert.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def escape_cell(value: str) -> str:
    """Return ``value`` with a leading ``'`` if a spreadsheet would run it."""
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def _escaped(row: list[str]) -> list[str]:
    return [escape_cell(cell) for cell in row]


def serialize(table: ReportTable, fmt: str) -> bytes:
    if fmt == "xlsx":
        return to_xlsx(table)
    return to_csv(table)


def to_csv(table: ReportTable) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_escaped(table.headers))
    writer.writerows(_escaped(row) for row in table.rows)
    return buf.getvalue().encode("utf-8-sig")  # BOM → Excel opens UTF-8 cleanly


def to_xlsx(table: ReportTable) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = table.title[:31]  # Excel sheet-name limit
    ws.append(_escaped(table.headers))
    for row in table.rows:
        # Escaped text never starts with "=", so openpyxl stores it as a
        # string cell, never as a formula.
        ws.append(_escaped(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
