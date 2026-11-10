"""Monthly flight-plan template workbook (F-04, owner request 2026-11).

Staff fill a month of flights in Excel: one row per active flight preset, one
column per day of the month, an ``x`` on the days that preset flies. The same
file goes back through ``POST /flights/import`` (``flight_plan_parser``).

Layout (sheet ``FlightPlan``) — the parser relies on the cells marked *:
  A1  label "Month"            B1* month as TEXT ``YYYY-MM``
  D1  instruction, merged across the day columns
  A2..C2 column titles         D2..* the integers 1..N (N = days in month)
  D3..  short weekday under each day
  A4.. preset label, B4..* arrival FLT, C4..* departure FLT, D4..* marks

Pure: no DB. Visible texts come from the i18n catalog in the request's
language; the parser never reads them, so the language does not matter.
"""

from __future__ import annotations

import calendar
import io
from datetime import date
from typing import NamedTuple

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from app.core.i18n import t

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SHEET_TITLE = "FlightPlan"
# Fixed coordinates shared with the parser.
FIRST_DAY_COL = 4  # column D
HEADER_ROW = 2
FIRST_DATA_ROW = 4
MARK = "x"

_BOLD = Font(bold=True)
_WEEKEND_FILL = PatternFill("solid", start_color="EDEDED", end_color="EDEDED")
_THIN = Side(style="thin", color="BFBFBF")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
_CENTER = Alignment(horizontal="center", vertical="center")


class TemplateRow(NamedTuple):
    """One preset row: its texts and the day numbers to prefill with ``x``."""

    label: str
    flt_arr: int
    flt_dep: int
    marked_days: set[int]


def template_filename(year: int, month: int) -> str:
    return f"flight-plan-{year}-{month:02d}.xlsx"


def _write_header(ws, year: int, month: int, n_days: int) -> None:
    last_col = get_column_letter(FIRST_DAY_COL + n_days - 1)
    ws["A1"] = t("flight.template_month_label")
    ws["A1"].font = _BOLD
    # Text, not a date: Excel would otherwise turn "2026-11" into a date and
    # the parser could no longer recognise the plan format.
    ws["B1"] = f"{year}-{month:02d}"
    ws["B1"].number_format = "@"
    ws["B1"].font = _BOLD
    ws["D1"] = t("flight.template_instruction")
    ws.merge_cells(f"D1:{last_col}1")

    titles = (
        t("flight.template_col_preset"),
        t("flight.template_col_arrival"),
        t("flight.template_col_departure"),
    )
    for col, title in enumerate(titles, start=1):
        ws.cell(row=HEADER_ROW, column=col, value=title)

    weekdays = t("flight.template_weekdays").split(",")
    for day in range(1, n_days + 1):
        col = FIRST_DAY_COL + day - 1
        ws.cell(row=HEADER_ROW, column=col, value=day)
        ws.cell(row=HEADER_ROW + 1, column=col, value=weekdays[date(year, month, day).weekday()])


def _style_grid(ws, year: int, month: int, n_days: int, last_row: int) -> None:
    last_col = FIRST_DAY_COL + n_days - 1
    for row in ws.iter_rows(min_row=HEADER_ROW, max_row=last_row, max_col=last_col):
        for cell in row:
            cell.border = _BORDER
            if cell.row <= HEADER_ROW + 1:
                cell.font = _BOLD
            if cell.column >= FIRST_DAY_COL:
                cell.alignment = _CENTER
                day = cell.column - FIRST_DAY_COL + 1
                if date(year, month, day).weekday() >= 5:  # Saturday / Sunday
                    cell.fill = _WEEKEND_FILL

    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 13
    ws.column_dimensions["C"].width = 13
    for col in range(FIRST_DAY_COL, last_col + 1):
        ws.column_dimensions[get_column_letter(col)].width = 4.5
    ws.freeze_panes = f"{get_column_letter(FIRST_DAY_COL)}{FIRST_DATA_ROW}"

    if last_row >= FIRST_DATA_ROW:
        # A dropdown steers people to "x"; the parser still validates every cell.
        marks = DataValidation(type="list", formula1='"x,X"', allow_blank=True)
        first = f"{get_column_letter(FIRST_DAY_COL)}{FIRST_DATA_ROW}"
        marks.add(f"{first}:{get_column_letter(last_col)}{last_row}")
        ws.add_data_validation(marks)


def build_template(year: int, month: int, rows: list[TemplateRow]) -> bytes:
    """Return the .xlsx bytes of the plan template for ``year``/``month``."""
    n_days = calendar.monthrange(year, month)[1]
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_TITLE
    _write_header(ws, year, month, n_days)

    for offset, row in enumerate(rows):
        r = FIRST_DATA_ROW + offset
        ws.cell(row=r, column=1, value=row.label)
        ws.cell(row=r, column=2, value=row.flt_arr)
        ws.cell(row=r, column=3, value=row.flt_dep)
        for day in row.marked_days:
            ws.cell(row=r, column=FIRST_DAY_COL + day - 1, value=MARK)

    _style_grid(ws, year, month, n_days, FIRST_DATA_ROW + len(rows) - 1)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
