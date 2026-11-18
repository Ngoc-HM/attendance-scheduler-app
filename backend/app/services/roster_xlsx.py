"""Write the month's roster in the customer's workbook layout (#70).

Same structure as the customer's ``WR <MON><YY>`` file: title and header
rows, one or two rows per day (one per flight pair) with merged day, weekday,
notes and person cells, a black spacer, the legend that doubles as the count
rows, the compensation-day rows, the signature line, the comp-day notes and
the ``AL <YY>`` leave overview. Rows below the day block move with it.
"""

from __future__ import annotations

import io
import statistics
from collections.abc import Sequence

from openpyxl import Workbook
from openpyxl.styles import Alignment, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from app.models.enums import AttendanceCode as C
from app.services.report_serializers import escape_cell
from app.services.roster_sheet import RosterFlightRow, RosterSheet
from app.services.roster_xlsx_leave import write_leave_sheet
from app.services.roster_xlsx_style import (
    BLACK,
    CENTER,
    CODE_FILL,
    COL_WIDTHS,
    COMP_LABELS,
    FIRST_PERSON_COL,
    H_HEADER,
    H_ROW,
    H_SIGNATURE,
    H_SPACER,
    H_TITLE,
    LEFT,
    LEGEND,
    MONTH_ABBR,
    PERSON_WIDTH,
    THICK,
    THIN,
    WEEKDAYS,
    WEEKEND,
    WHITE,
    border,
    style,
)


def sheet_name(year: int, month: int) -> str:
    return f"{MONTH_ABBR[month - 1]}{year % 100:02d}"


def file_name(year: int, month: int) -> str:
    return f"WR {sheet_name(year, month)}.xlsx"


class _Writer:
    def __init__(self, ws: Worksheet, data: RosterSheet) -> None:
        self.ws, self.data = ws, data
        self.cols = [FIRST_PERSON_COL + i for i in range(len(data.people))]
        self.last_col = self.cols[-1] if self.cols else 5
        roles = [p.role for p in data.people]
        # Thick separator wherever the role changes, and on the outer edge.
        self.sides = [
            (THICK if i and roles[i - 1] != r else THIN,
             THICK if i == len(roles) - 1 or roles[i + 1] != r else THIN)
            for i, r in enumerate(roles)
        ]
        days = [d.day for d in data.days]
        self.counts = [
            {c: sum(1 for d in days if data.grid.get((p.user_id, d)) is c) for c in C}
            for p in data.people
        ]
        x = [n[C.X] for n in self.counts]
        self.off_days = statistics.median_low(x) if x else 0

    def person_box(self, i: int, top=THIN, bottom=THIN):
        return border(self.sides[i][0], self.sides[i][1], top, bottom)

    def setup(self) -> None:
        ws = self.ws
        for letter, width in COL_WIDTHS.items():
            ws.column_dimensions[letter].width = width
        for col in self.cols:
            ws.column_dimensions[get_column_letter(col)].width = PERSON_WIDTH
        ws.page_setup.paperSize = 9
        ws.page_setup.orientation = "portrait"
        ws.page_setup.scale = 68
        ws.page_setup.fitToWidth = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        m = ws.page_margins
        m.left, m.right, m.top, m.bottom, m.header, m.footer = 0.25, 0, 0.5, 0.5, 0.05, 0
        ws.sheet_view.zoomScale = 80

    def title_and_header(self) -> None:
        ws, d = self.ws, self.data
        working = len(d.days) - self.off_days
        style(ws.cell(1, 1, f"WR {sheet_name(d.year, d.month)} // (TTL {working} WORKING DAYS)"),
              size=14, bold=True, bg=WHITE)
        # The customer's title spans up to the second-to-last person column.
        ws.merge_cells(start_row=1, start_column=1, end_row=1,
                       end_column=max(5, self.last_col - 1))
        ws.row_dimensions[1].height = H_TITLE
        for col, text in enumerate(["Date", "Day", "FLT #", "STA/STD LT FRA", "NOTES"], 1):
            cell = style(ws.cell(2, col, text), bold=True, bg=WHITE, box=border())
            if col == 4:
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for i, (col, p) in enumerate(zip(self.cols, d.people, strict=True)):
            style(ws.cell(2, col, escape_cell(p.code)), bold=True, bg=WHITE,
                  box=self.person_box(i))
        ws.row_dimensions[2].height = H_HEADER

    def day_block(self) -> int:
        ws, d, row = self.ws, self.data, 3
        # The carry days follow the last day, dated day/month (owner
        # 2026-11-18); they stay out of every count below.
        for day in [*d.days, *d.carry_days]:
            flights: list[RosterFlightRow | None] = list(day.flights) or [None]
            span = len(flights)
            weekend = day.day.weekday() >= 5
            for k, flight in enumerate(flights):
                r = row + k
                style(ws.cell(r, 3, flight.label if flight else None), box=border())
                style(ws.cell(r, 4, flight.times if flight else None), box=border())
                ws.row_dimensions[r].height = H_ROW
            bg = WEEKEND if weekend else None
            label = (
                str(day.day.day)
                if day.day.month == d.month
                else f"{day.day.day}/{day.day.month}"
            )
            style(ws.cell(row, 1, label), bg=bg, box=border())
            style(ws.cell(row, 2, WEEKDAYS[day.day.weekday()]), bg=bg, box=border())
            style(ws.cell(row, 5), box=border(),
                  align=Alignment(horizontal="center", vertical="center", wrap_text=True))
            for i, (col, p) in enumerate(zip(self.cols, d.people, strict=True)):
                code = d.grid.get((p.user_id, day.day))
                style(ws.cell(row, col, code.value if code else None),
                      bg=CODE_FILL.get(code) if code else None, box=self.person_box(i))
            if span > 1:
                for col in [1, 2, 5, *self.cols]:
                    ws.merge_cells(start_row=row, start_column=col,
                                   end_row=row + span - 1, end_column=col)
            row += span
        return row - 1

    def spacer(self, r: int) -> None:
        """The black bar under the day block (open at the bottom under A..D,
        as in the customer's file)."""
        for col in range(1, 6):
            style(self.ws.cell(r, col), bg=BLACK, box=border(bottom=Side()) if col < 5
                  else border(right=Side()))
        for i, col in enumerate(self.cols):
            style(self.ws.cell(r, col), bg=BLACK, box=self.person_box(i))
        self.ws.row_dimensions[r].height = H_SPACER

    def legend_label(self, r: int, text: str, *, size: float = 10, color=None, bg=WHITE,
                     align=LEFT, merge: bool = True, bottom=THIN) -> None:
        style(self.ws.cell(r, 1, text), size=size, bold=True, color=color, bg=bg,
              align=align, box=border(right=THIN if merge else Side(), bottom=bottom))
        if merge:
            self.ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        else:  # the customer's A/D row: four filled cells, not merged
            for col in (2, 3, 4):
                style(self.ws.cell(r, col), size=size, bold=True, bg=bg, align=align,
                      box=border(left=Side(), right=THIN if col == 4 else Side()))
        style(self.ws.cell(r, 5), bold=True, bg=WHITE,
              box=border(left=Side(), right=Side(), bottom=bottom))
        self.ws.row_dimensions[r].height = H_ROW

    def values(self, r: int, values: Sequence[int | None], bg=None, bottom=THIN) -> None:
        for i, (col, value) in enumerate(zip(self.cols, values, strict=True)):
            style(self.ws.cell(r, col, value), bold=True, fmt="0", bg=bg,
                  box=self.person_box(i, bottom=bottom))

    def legend(self, r: int) -> int:
        has_ad = any(n[C.AD] for n in self.counts)
        for code, text, size, color, bg in LEGEND:
            if code is C.AD and not has_ad:
                continue
            self.legend_label(r, text, size=size, color=color, bg=bg,
                              merge=code is not C.A_D, align=Alignment(
                                  horizontal="left", vertical="top", wrap_text=True)
                              if code is C.A else LEFT)
            fill_counts = bg if code in (C.CD, C.AL) else None
            self.values(r, [n[code] for n in self.counts], bg=fill_counts)
            r += 1
        none = Side(style=None)
        self.legend_label(r, f"X = OFF DAY (INCL PH): {self.off_days:02d} DAYS", size=9,
                          bottom=none)
        self.values(r, [None] * len(self.cols), bottom=none)
        r += 1
        self.legend_label(r, "TTL DAYS", size=12, align=CENTER)
        self.values(r, [len(self.data.days) - n[C.X] for n in self.counts])
        return r + 1

    def comp(self, r: int) -> int:
        d = self.data
        rows = [d.comp[p.user_id] for p in d.people]
        figures = [[c.present for c in rows], [c.previous for c in rows],
                   [c.used for c in rows], [c.total for c in rows]]
        for label, values in zip(COMP_LABELS, figures, strict=True):
            style(self.ws.cell(r, 1, label), bold=True, bg=WHITE, align=LEFT, box=border())
            for col in (2, 3):
                style(self.ws.cell(r, col), bg=WHITE, box=border())
            style(self.ws.cell(r, 4), bold=True, bg=WHITE, align=LEFT,
                  box=border(right=Side()))
            style(self.ws.cell(r, 5), bold=True, bg=WHITE, align=LEFT,
                  box=border(left=Side(), right=Side()))
            self.values(r, values)
            self.ws.row_dimensions[r].height = H_ROW
            r += 1
        return r

    def footer(self, r: int) -> None:
        ws, d = self.ws, self.data
        sig = r + 1
        style(ws.cell(sig, 1, f"Checked by {escape_cell(d.checked_by)} on:"), size=14,
              bold=True, bg=WHITE, align=LEFT)
        style(ws.cell(sig, 10, "Approved by GM on:"), size=14, bold=True, color=BLACK,
              fmt="General", align=None)
        ws.row_dimensions[sig].height = H_SIGNATURE
        heading = sig + 2
        style(ws.cell(heading, 1, d.comp_heading), name="Calibri", size=12, bold=True,
              color=BLACK, fmt="General", align=None)
        ws.row_dimensions[heading].height = H_ROW
        ws.row_dimensions[heading + 1].height = H_SPACER
        for k, line in enumerate(d.comp_notes):
            style(ws.cell(heading + 2 + k, 1, escape_cell(line)), name="Calibri", size=11,
                  color=BLACK, fmt="General", align=None)


def build_workbook(data: RosterSheet) -> bytes:
    wb = Workbook()
    wb.properties.creator = "Attendance Scheduler"
    ws = wb.active
    ws.title = sheet_name(data.year, data.month)
    w = _Writer(ws, data)
    w.setup()
    w.title_and_header()
    last = w.day_block()
    w.spacer(last + 1)
    after_legend = w.legend(last + 2)
    w.footer(w.comp(after_legend))
    write_leave_sheet(wb.create_sheet(f"AL {data.year % 100:02d}"), data)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
