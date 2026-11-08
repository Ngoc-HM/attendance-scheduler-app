"""Excel workbook parser for the monthly flight import (F-04, §8).

Expected layout (row 1 = header, one flight per data row):
  Column A: date       — Excel date cell OR ISO string "YYYY-MM-DD"
  Column B: flt_number — integer (37, 36, 31, 30)
  Column C: route      — string, e.g. "HAN-FRA" (optional, at most
                         ROUTE_MAX_LENGTH characters)
  Column D: sta        — Excel time cell OR "HH:MM" string (optional, LT FRA)
  Column E: std        — Excel time cell OR "HH:MM" string (optional, LT FRA)

This module is pure I/O parsing with no DB dependency, making it unit-testable
in isolation from SQLAlchemy. Row messages come from the i18n catalog
(``flight.import_row_*``) in the request's language.
"""

from __future__ import annotations

import io
from datetime import date, datetime, time
from typing import Any, NamedTuple

from app.core.i18n import t

# ``Flight.route`` is String(32): a longer value is a row error here instead of
# a database error at commit (PostgreSQL enforces the length; SQLite does not).
ROUTE_MAX_LENGTH = 32

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

# Longest cell text echoed back in an error message (keeps responses small).
_MAX_ECHO = 40


class FlightParseResult(NamedTuple):
    """Outcome of :func:`parse_flight_workbook` (unpacks as a 3-tuple)."""

    rows: list[dict]
    errors: list[str]
    warnings: list[str]


def _echo(value: Any) -> str:
    """Cell value as short text for an error message."""
    text = "" if value is None else str(value).strip()
    return text if len(text) <= _MAX_ECHO else text[: _MAX_ECHO - 1] + "…"


def parse_flight_workbook(raw: bytes) -> FlightParseResult:
    """Parse raw .xlsx bytes into a list of flight dicts.

    Args:
        raw: Raw bytes of a valid .xlsx file.

    Returns:
        ``(rows, errors, warnings)`` where:
          - rows: dicts with keys day/flt_number/route/sta/std, at most one
            per (day, flt_number) — a repeated key keeps the LAST row's data
            at the position of its first occurrence (review B5).
          - errors: translated row-level messages (i18n keys
            ``flight.import_row_*`` with ``row``/``value`` parameters).
          - warnings: translated ``flight.import_row_duplicate`` messages, one
            per repeated row.

    If errors is non-empty, rows may be incomplete — callers should abort
    the import and report the errors without committing.
    """
    import openpyxl  # local import so the module loads without openpyxl installed

    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb.active

    rows_iter = iter(ws.iter_rows(values_only=True))
    next(rows_iter, None)  # skip header row

    parse_errors: list[str] = []
    warnings: list[str] = []
    by_key: dict[tuple[date, int], dict] = {}
    first_row_of: dict[tuple[date, int], int] = {}

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
        except (ValueError, TypeError):
            parse_errors.append(
                t("flight.import_row_invalid_date").format(
                    row=row_idx, value=_echo(col_date)
                )
            )
            continue

        # flt_number — required.
        try:
            flt_number = int(col_flt)  # type: ignore[arg-type]
        except (ValueError, TypeError):
            parse_errors.append(
                t("flight.import_row_invalid_flt").format(
                    row=row_idx, value=_echo(col_flt)
                )
            )
            continue

        # Optional time columns.
        times: list[time | None] = []
        for col_time in (col_sta, col_std):
            try:
                times.append(parse_time_cell(col_time))
            except (ValueError, TypeError):
                parse_errors.append(
                    t("flight.import_row_invalid_time").format(
                        row=row_idx, value=_echo(col_time)
                    )
                )
                break
        if len(times) < 2:  # noqa: PLR2004
            continue
        sta, std = times

        route = str(col_route).strip() if col_route is not None else None
        if route is not None and len(route) > ROUTE_MAX_LENGTH:
            parse_errors.append(
                t("flight.import_row_route_too_long").format(
                    row=row_idx, max=ROUTE_MAX_LENGTH
                )
            )
            continue

        key = (day, flt_number)
        if key in by_key:
            warnings.append(
                t("flight.import_row_duplicate").format(
                    row=row_idx, first_row=first_row_of[key], flt=flt_number
                )
            )
        else:
            first_row_of[key] = row_idx
        by_key[key] = {
            "day": day,
            "flt_number": flt_number,
            "route": route,
            "sta": sta,
            "std": std,
        }

    return FlightParseResult(list(by_key.values()), parse_errors, warnings)
