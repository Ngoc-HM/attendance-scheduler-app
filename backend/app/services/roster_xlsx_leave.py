"""The ``AL <YY>`` sheet of the roster workbook: annual leave per month (#70).

Same layout as the customer's sheet (German labels kept): codes across,
months down, the quota above and what is left below. Days are approved
leave requests of the roster's year.
"""

from __future__ import annotations

from openpyxl.styles import Alignment, Font, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from app.services.report_serializers import escape_cell
from app.services.roster_sheet import RosterSheet
from app.services.roster_xlsx_style import border

GERMAN_MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
                 "September", "Oktober", "November", "Dezember"]
WIDTH, LAST_WIDTH, DEFAULT_WIDTH = 25.7109375, 24.28515625, 11.42578125
CENTER = Alignment(horizontal="center", vertical="center")


def _cell(ws: Worksheet, row: int, col: int, value=None, *, bold=False, size=11, box=None):
    cell = ws.cell(row, col, value)
    cell.font = Font(name="Calibri", size=size, bold=bold)
    cell.alignment = CENTER
    if box is not None:
        cell.border = box
    return cell


def write_leave_sheet(ws: Worksheet, data: RosterSheet) -> None:
    people = data.people
    cols = [3 + i for i in range(len(people))]
    ws.sheet_format.defaultColWidth = DEFAULT_WIDTH
    ws.column_dimensions["B"].width = WIDTH
    for i, col in enumerate(cols):
        last = i == len(cols) - 1
        ws.column_dimensions[get_column_letter(col)].width = LAST_WIDTH if last else WIDTH
    m = ws.page_margins
    m.left, m.right, m.top, m.bottom, m.header, m.footer = (
        0.7, 0.7, 0.787401575, 0.787401575, 0.3, 0.3)

    _cell(ws, 4, 3, f"Urlaubstageübersicht {data.year}", bold=True, size=16)
    ws.row_dimensions[4].height = 21
    none = Side()
    for col, p in zip(cols, people, strict=True):
        _cell(ws, 6, col, escape_cell(p.code), bold=True, size=12,
              box=border(bottom=none))
    ws.row_dimensions[6].height = 15.75
    _cell(ws, 7, 2, "Monat / U Tage", box=border())
    for col, p in zip(cols, people, strict=True):
        _cell(ws, 7, col, data.leave_quota.get(p.user_id, 0), bold=True,
              box=border(top=none))
    for m_index, name in enumerate(GERMAN_MONTHS, 1):
        row = 7 + m_index
        box = border(bottom=none) if m_index == 12 else border()
        _cell(ws, row, 2, name, box=box)
        for col, p in zip(cols, people, strict=True):
            days = data.leave_days.get(p.user_id, {}).get(m_index)
            _cell(ws, row, col, days or None, box=box)
    ws.row_dimensions[19].height = 15.75
    rest = border(top=Side(style="medium"))
    _cell(ws, 20, 2, "Rest", bold=True, box=rest)
    for col, p in zip(cols, people, strict=True):
        used = sum(data.leave_days.get(p.user_id, {}).values())
        _cell(ws, 20, col, data.leave_quota.get(p.user_id, 0) - used, bold=True, box=rest)
