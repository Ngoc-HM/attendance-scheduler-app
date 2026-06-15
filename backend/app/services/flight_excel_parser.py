"""Excel workbook parser for the monthly flight import (F-04, §8).

Expected layout (row 1 = header, one flight per data row):
  Column A: date       — Excel date cell OR ISO string "YYYY-MM-DD"
  Column B: flt_number — integer (37, 36, 31, 30)
  Column C: route      — string, e.g. "HAN-FRA" (optional)
  Column D: sta        — Excel time cell OR "HH:MM" string (optional, LT FRA)
  Column E: std        — Excel time cell OR "HH:MM" string (optional, LT FRA)

This module is pure I/O parsing with no DB dependency, making it unit-testable
in isolation from SQLAlchemy.
"""

from __future__ import annotations

import io
from datetime import date, datetime, time
from typing import Any


# ---------------------------------------------------------------------------
# Cell value parsers
# ---------------------------------------------------------------------------


def parse_date_cell(value: Any) -> date:
    """Parse a date from an openpyxl cell value (datetime/date/str).

    Raises ValueError if the value cannot be interpreted as a date.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.strip())
    raise ValueError(f"Cannot parse date from {value!r}")


def parse_time_cell(value: Any) -> time | None:
    """Parse an optional time from an openpyxl cell value.

    Accepts: time object, datetime object (extracts .time()), or "HH:MM"/"HH:MM:SS" string.
    Returns None for None or empty string inputs.
    Raises ValueError on unrecognisable formats.
    """
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        parts = stripped.split(":")
        if len(parts) < 2:  # noqa: PLR2004
            raise ValueError(f"Cannot parse time from {value!r}")
        return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    raise ValueError(f"Cannot parse time from {value!r}")


# ---------------------------------------------------------------------------
# Workbook row parser
# ---------------------------------------------------------------------------


def parse_flight_workbook(raw: bytes) -> tuple[list[dict], list[str]]:
    """Parse raw .xlsx bytes into a list of flight dicts.

    Args:
        raw: Raw bytes of a valid .xlsx file.

    Returns:
        (parsed_rows, parse_errors) where:
          - parsed_rows: list of dicts with keys day/flt_number/route/sta/std.
          - parse_errors: list of human-readable row-level error strings.

    If parse_errors is non-empty, parsed_rows may be incomplete — callers
    should abort the import and report the errors without committing.
    """
    import openpyxl  # local import so the module loads without openpyxl installed

    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.active

    rows_iter = iter(ws.iter_rows(values_only=True))
    next(rows_iter, None)  # skip header row

    parse_errors: list[str] = []
    parsed_rows: list[dict] = []

    for row_idx, row in enumerate(rows_iter, start=2):
        # Skip entirely empty rows.
        if not row or all(v is None for v in row):
            continue

        col_date = row[0] if len(row) > 0 else None
        col_flt = row[1] if len(row) > 1 else None
        col_route = row[2] if len(row) > 2 else None
        col_sta = row[3] if len(row) > 3 else None
        col_std = row[4] if len(row) > 4 else None

        # date — required.
        try:
            day = parse_date_cell(col_date)
        except (ValueError, TypeError) as exc:
            parse_errors.append(f"Row {row_idx}: invalid date — {exc}")
            continue

        # flt_number — required.
        try:
            flt_number = int(col_flt)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            parse_errors.append(f"Row {row_idx}: invalid flt_number — {col_flt!r}")
            continue

        # Optional time columns.
        try:
            sta = parse_time_cell(col_sta)
            std = parse_time_cell(col_std)
        except (ValueError, TypeError) as exc:
            parse_errors.append(f"Row {row_idx}: invalid time — {exc}")
            continue

        parsed_rows.append(
            {
                "day": day,
                "flt_number": flt_number,
                "route": str(col_route).strip() if col_route is not None else None,
                "sta": sta,
                "std": std,
            }
        )

    return parsed_rows, parse_errors
