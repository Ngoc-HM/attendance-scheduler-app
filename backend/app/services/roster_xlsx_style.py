"""Styling constants of the customer's roster workbook (#70).

Values copied from the customer's ``WR NOV26`` file (theme colours resolved
to plain RGB). Edit here to change the look; ``roster_xlsx`` only places.
"""

from __future__ import annotations

from openpyxl.cell.cell import Cell
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from app.models.enums import AttendanceCode as C

TNR = "Times New Roman"
TEXT = "@"
WHITE, BLACK = "FFFFFF", "000000"
WEEKEND = "C6E0B4"  # Sat/Sun date and weekday cells
# Legend colours, applied to every cell holding the code. AD is not in the
# customer's legend: it gets the fill of the closest working code (A/D, the
# other double shift) and a legend line of its own.
CODE_FILL: dict[C, str] = {
    C.A_D: "FF99CC",
    C.AD: "FF99CC",
    C.CD: "F8CBAD",
    C.O_D: "9DC3E6",
    C.AL: "FFFF00",
}

COL_WIDTHS = {"A": 7.7109375, "B": 7.7109375, "C": 8.7109375, "D": 10.7109375,
              "E": 23.7109375}
PERSON_WIDTH = 8.7109375
FIRST_PERSON_COL = 6  # F
H_TITLE, H_HEADER, H_ROW, H_SPACER, H_SIGNATURE = 18.75, 31.5, 15.75, 5.1, 18.75

THIN, THICK = Side(style="thin"), Side(style="thick")
CENTER = Alignment(horizontal="center", vertical="center")
LEFT = Alignment(horizontal="left", vertical="center")


def fill(rgb: str) -> PatternFill:
    return PatternFill(fill_type="solid", start_color="FF" + rgb, end_color="FF" + rgb)


def border(left=THIN, right=THIN, top=THIN, bottom=THIN) -> Border:
    return Border(left=left, right=right, top=top, bottom=bottom)


def style(cell: Cell, *, size: float = 12, bold: bool = False, color: str | None = None,
          name: str = TNR, fmt: str = TEXT, align: Alignment | None = CENTER,
          bg: str | None = None, box: Border | None = None) -> Cell:
    cell.font = Font(name=name, size=size, bold=bold,
                     color=("FF" + color) if color else None)
    cell.number_format = fmt
    if align is not None:
        cell.alignment = align
    if bg is not None:
        cell.fill = fill(bg)
    if box is not None:
        cell.border = box
    return cell


MONTH_ABBR = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT",
              "NOV", "DEC"]
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
# Legend lines in the customer's words (spacing kept); each row also counts
# the code per person. (code, text, font size, font colour, fill)
LEGEND = [
    (C.A, "A= ARR duty // till STD - 60 Minutes", 10, None, WHITE),
    (C.D, "D = DEP duty  // Briefing Time - 40MIN", 10, "FF0000", WHITE),
    (C.A_D, "A/D = ARR and DEP duty // 2 working days", 10, None, "FF99CC"),
    (C.AD, "AD = ARR and DEP duty // no compensation day", 10, None, "FF99CC"),
    (C.CD, "CD = compensation days ", 10, None, "F8CBAD"),
    (C.O_D, "O/D = office duty", 10, None, "9DC3E6"),
    (C.T, "T = online/trainings course", 10, None, WHITE),
    (C.S, "S = reported SICK", 10, None, WHITE),
    (C.B, "B = Business Trip", 10, None, WHITE),
    (C.AL, "AL = on leave", 10, None, "FFFF00"),
]
COMP_LABELS = ["compensation days present month", "compensation days previous month ",
               "compensation days (CD) used this month", "compensation days (CD) in TTL"]
