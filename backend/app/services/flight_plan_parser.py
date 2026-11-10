"""Parser for the filled monthly flight-plan template (F-04, owner 2026-11).

See ``flight_plan_template.py`` for the layout. ``POST /flights/import``
accepts both this "plan" and the older one-flight-per-row list
(``flight_excel_parser.py``); a workbook is a plan when B1 of the active sheet
is the text ``YYYY-MM`` (``read_plan``), anything else keeps the list format.

Pure: no DB, raises nothing for bad content — it returns translated messages
(``flight.plan_*``) like the list parser. Only the coordinates are read, never
the titles, so a template downloaded in either language parses the same.
"""

from __future__ import annotations

import calendar
import io
import re
from typing import Any, NamedTuple

from openpyxl.utils import get_column_letter

from app.core.i18n import t
from app.schemas.common import YEAR_MAX, YEAR_MIN
from app.services.flight_excel_parser import _echo
from app.services.flight_plan_template import FIRST_DATA_ROW, FIRST_DAY_COL, HEADER_ROW

_MONTH_TEXT = re.compile(r"^\d{4}-\d{2}$")


class PlanRow(NamedTuple):
    """One data row: its sheet row number, the preset pair and marked days."""

    row: int
    flt_arr: int
    flt_dep: int
    days: frozenset[int]


class PlanParseResult(NamedTuple):
    year: int
    month: int
    rows: list[PlanRow]
    errors: list[str]


def _cell(row: tuple, col: int) -> Any:
    """Value of the 1-based column ``col`` of a values-only row (None if short)."""
    return row[col - 1] if len(row) >= col else None


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _as_int(value: Any) -> int | None:
    """int, integral float or numeric text → int; anything else → None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        text = value.strip()
        try:
            return int(text)
        except ValueError:
            try:
                number = float(text)
            except ValueError:
                return None
            return int(number) if number.is_integer() else None
    return None


def _header_ok(header: tuple, n_days: int) -> bool:
    """Row 2 lists exactly the days 1..N from column D, and no day N+1."""
    for day in range(1, n_days + 1):
        if _as_int(_cell(header, FIRST_DAY_COL + day - 1)) != day:
            return False
    # A number right after day N means the sheet was made for a longer month.
    return _as_int(_cell(header, FIRST_DAY_COL + n_days)) is None


def _parse_row(row_idx: int, row: tuple, n_days: int, errors: list[str]) -> PlanRow | None:
    pair: list[int] = []
    for col in (2, 3):
        value = _cell(row, col)
        number = _as_int(value)
        if number is None:
            errors.append(
                t("flight.plan_row_invalid_flt").format(
                    row=row_idx, col=get_column_letter(col), value=_echo(value)
                )
            )
        else:
            pair.append(number)

    days: set[int] = set()
    for day in range(1, n_days + 1):
        col = FIRST_DAY_COL + day - 1
        value = _cell(row, col)
        if _blank(value):
            continue
        if isinstance(value, str) and value.strip().lower() == "x":
            days.add(day)
        else:
            errors.append(
                t("flight.plan_bad_mark").format(
                    cell=f"{get_column_letter(col)}{row_idx}", value=_echo(value)
                )
            )
    if len(pair) < 2:  # noqa: PLR2004
        return None
    return PlanRow(row_idx, pair[0], pair[1], frozenset(days))


def read_plan(raw: bytes) -> PlanParseResult | None:
    """Parse ``raw`` as a plan, or return None when it is not one (list format).

    Raises only when openpyxl cannot read the file; the caller maps that to
    ``flight.import_bad_file``.
    """
    import openpyxl  # local import, as in flight_excel_parser

    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    rows = list(wb.active.iter_rows(values_only=True))
    b1 = _cell(rows[0], 2) if rows else None
    if not isinstance(b1, str) or not _MONTH_TEXT.match(b1.strip()):
        return None

    year, month = (int(part) for part in b1.strip().split("-"))
    if not (YEAR_MIN <= year <= YEAR_MAX and 1 <= month <= 12):  # noqa: PLR2004
        message = t("flight.plan_bad_month").format(
            value=_echo(b1), min=YEAR_MIN, max=YEAR_MAX
        )
        return PlanParseResult(year, month, [], [message])

    n_days = calendar.monthrange(year, month)[1]
    header = rows[HEADER_ROW - 1] if len(rows) >= HEADER_ROW else ()
    if not _header_ok(header, n_days):
        return PlanParseResult(year, month, [], [t("flight.plan_layout_changed")])

    errors: list[str] = []
    parsed: list[PlanRow] = []
    first_row_of: dict[tuple[int, int], int] = {}
    for row_idx, row in enumerate(rows[FIRST_DATA_ROW - 1:], start=FIRST_DATA_ROW):
        # Only columns A..last day count; notes further right are ignored.
        if all(_blank(_cell(row, col)) for col in range(1, FIRST_DAY_COL + n_days)):
            continue
        plan_row = _parse_row(row_idx, row, n_days, errors)
        if plan_row is None:
            continue
        key = (plan_row.flt_arr, plan_row.flt_dep)
        if key in first_row_of:
            errors.append(
                t("flight.plan_duplicate_pair").format(
                    row=row_idx, first_row=first_row_of[key], arr=key[0], dep=key[1]
                )
            )
            continue
        first_row_of[key] = row_idx
        parsed.append(plan_row)
    return PlanParseResult(year, month, parsed, errors)
