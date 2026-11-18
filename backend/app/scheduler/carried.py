"""Cells already decided, and the window's own month (owner 2026-11-18).

Generating month M plans M and the days of M+1 up to the Sunday that ends
M's last week. Those M+1 days ("carry days") are stored in M+1's schedule
as carried cells; generating M+1 later keeps them exactly as they are
(``SolverInput.fixed``) and plans the rest of the window around them.

Rules counted per month count over the window's OWN month (the calendar
month of its first day): the exact ordinary-X entitlement, owed comp days
and the two pure A days. The carry days get no X minimum and at most as
many X as they hold Saturdays and Sundays (``constraints_monthly_quota``);
no CD is granted on them. Rules that run along the calendar see the whole
window.

A fixed cell is pinned in the decision layer:

* a code of the person's domain → that code;
* any other working code (A/D, T, B, or a code of another group) → the
  person's first working code, and the staffing rules count it the way the
  persisted re-check counts the stored code (``cover``): A/D covers one A
  and one D for group A, every other foreign code covers nothing;
* a leave code (AL, S) is not fixed here: ``split`` moves it to
  ``approved_off`` so the counts treat it like approved leave, exactly as
  the re-check reads an AL/S cell.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import codes_for

LEAVE_CODES = (AttendanceCode.AL, AttendanceCode.S)


def own_days(inp: SolverInput) -> list[date]:
    """The window's days in the calendar month of its first day."""
    days = sorted(inp.days)
    if not days:
        return []
    return [d for d in days if (d.year, d.month) == (days[0].year, days[0].month)]


def ahead_days(inp: SolverInput) -> list[date]:
    """The window's carry days: everything after its own month."""
    own = set(own_days(inp))
    return [d for d in sorted(inp.days) if d not in own]


def split(
    cells: Mapping[int, Mapping[date, AttendanceCode]],
    roles: Mapping[int, Role],
) -> tuple[dict[int, dict[date, AttendanceCode]], dict[int, dict[date, AttendanceCode]]]:
    """Stored carried cells → (``fixed``, leave for ``approved_off``).

    Every non-working code outside the person's domain (AL, S) is leave;
    everything else is fixed. A user without a role is skipped.
    """
    fixed: dict[int, dict[date, AttendanceCode]] = {}
    leave: dict[int, dict[date, AttendanceCode]] = {}
    for uid, by_day in cells.items():
        role = roles.get(uid)
        if role is None:
            continue
        domain = codes_for(role)
        for day, code in by_day.items():
            if code not in domain and not code.is_working:
                leave.setdefault(uid, {})[day] = code
            else:
                fixed.setdefault(uid, {})[day] = code
    return fixed, leave


def foreign_work(inp: SolverInput) -> dict[tuple[int, date], AttendanceCode]:
    """Fixed working cells whose code is outside the person's domain."""
    roles = {p.user_id: p.role for p in inp.people}
    return {
        (uid, day): code
        for uid, by_day in inp.fixed.items()
        if uid in roles
        for day, code in by_day.items()
        if code.is_working and code not in codes_for(roles[uid])
    }


def cover(code: AttendanceCode) -> tuple[int, int]:
    """(A, D) flight cover of a foreign code held by a group-A person, as
    ``schedule_violation_checker.check_staffing`` counts it."""
    return (1, 1) if code is AttendanceCode.A_D else (0, 0)


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> None:
    """Pin every fixed cell of the window. HARD: these days are facts."""
    roles = {p.user_id: p.role for p in inp.people}
    window = set(inp.days)
    for uid, by_day in inp.fixed.items():
        if uid not in roles:
            continue
        domain = codes_for(roles[uid])
        for day, code in by_day.items():
            if day not in window:
                continue
            if code in domain:
                model.add(x[(uid, day, code)] == 1)
            elif code.is_working:
                first = next(c for c in domain if c.is_working)
                model.add(x[(uid, day, first)] == 1)
            else:
                # Leave belongs in approved_off (``split``); a stray one is
                # still a rest day.
                model.add(x[(uid, day, AttendanceCode.X)] == 1)
