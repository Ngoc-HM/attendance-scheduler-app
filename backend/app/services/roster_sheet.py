"""Data of the monthly roster in the customer's workbook layout (#70).

Plain dataclasses filled by ``roster_report`` and written by ``roster_xlsx``,
so the layout code never touches the database. People appear only by their
person code (A1, F2, M1 ...): no name ever reaches the file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.models.enums import AttendanceCode


@dataclass(frozen=True)
class RosterPerson:
    user_id: int
    code: str
    role: str  # Role value; a role change draws a thick separator


@dataclass(frozen=True)
class RosterFlightRow:
    """One flight pair of a day, e.g. ``31/30`` with ``0650/1305``."""

    label: str
    times: str


@dataclass(frozen=True)
class RosterDay:
    day: date
    # One row per pair; an empty list still gives the day one (empty) row.
    flights: list[RosterFlightRow]


@dataclass(frozen=True)
class CompRow:
    """The four compensation-day figures of one person."""

    present: int   # earned this month (A/D, holiday work)
    previous: int  # balance at the start of the month
    used: int      # CD days this month
    total: int     # balance after the month


@dataclass
class RosterSheet:
    year: int
    month: int
    people: list[RosterPerson]
    days: list[RosterDay]
    # Includes the carry days' cells (keys dated in the next month).
    grid: dict[tuple[int, date], AttendanceCode]
    comp: dict[int, CompRow]
    # "Compensation Days from <previous month> as follows:" lines.
    comp_heading: str
    comp_notes: list[str]
    checked_by: str  # code of the admin who downloads
    # Second sheet: approved leave days per person and month of the year.
    leave_days: dict[int, dict[int, int]] = field(default_factory=dict)
    leave_quota: dict[int, int] = field(default_factory=dict)
    # The next month's days up to the Sunday ending this month's last week
    # (owner 2026-11-18), printed after the last day; not in any count.
    carry_days: list[RosterDay] = field(default_factory=list)
