"""Neutral tabular report model + aggregation (F-15).

A ``ReportTable`` is format-agnostic (title + headers + rows). Serializers
(CSV/XLSX) render it, so a new layout is a new serializer — never a change to
the data assembly (spec §4.7: layout deferred / kept flexible).

Working-day totals use ``AttendanceCode.workday_value`` (A/D counts as 2, §7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.models.enums import AttendanceCode


@dataclass
class ReportTable:
    title: str
    headers: list[str]
    rows: list[list[str]] = field(default_factory=list)


@dataclass(frozen=True)
class UserRow:
    user_id: int
    name: str
    role: str


def _working_days(codes: list[AttendanceCode]) -> int:
    return sum(c.workday_value for c in codes)


def build_monthly(
    users: list[UserRow],
    days: list[date],
    grid: dict[tuple[int, date], AttendanceCode],
) -> ReportTable:
    """Person × day matrix + per-person totals for one month."""
    day_cols = [str(d.day) for d in days]
    headers = ["User", "Role", *day_cols, "Work days", "A/D", "Off (X)"]
    table = ReportTable(title=f"Attendance {days[0].year}-{days[0].month:02d}", headers=headers)

    for u in users:
        codes = [grid.get((u.user_id, d)) for d in days]
        cells = [c.value if c else "" for c in codes]
        present = [c for c in codes if c is not None]
        work = _working_days(present)
        ad = sum(1 for c in present if c is AttendanceCode.A_D)
        off = sum(1 for c in present if c is AttendanceCode.X)
        table.rows.append([u.name, u.role, *cells, str(work), str(ad), str(off)])

    return table


def build_yearly(
    users: list[UserRow],
    year: int,
    grids_by_month: dict[int, dict[tuple[int, date], AttendanceCode]],
) -> ReportTable:
    """Person × month working-day totals for a full year."""
    headers = ["User", "Role", *[f"M{m}" for m in range(1, 13)], "Total"]
    table = ReportTable(title=f"Attendance {year}", headers=headers)

    for u in users:
        monthly_totals: list[int] = []
        for m in range(1, 13):
            grid = grids_by_month.get(m, {})
            codes = [c for (uid, _), c in grid.items() if uid == u.user_id]
            monthly_totals.append(_working_days(codes))
        table.rows.append(
            [u.name, u.role, *map(str, monthly_totals), str(sum(monthly_totals))]
        )

    return table
