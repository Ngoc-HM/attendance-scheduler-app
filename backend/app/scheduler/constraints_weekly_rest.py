"""Rule W — at most 5 working days in every calendar week, Mon–Sun (owner 2026-11-12).

Owner: "không làm việc quá 5 ngày 1 tuần … không nhất thiết phải trong 1
tháng". Every Monday-to-Sunday week holds at least 2 rest days, which need
NOT be adjacent. It replaces the ROLLING reading ("any 7 consecutive days",
``rolling_seven_min_two_rest``), which together with the month's fixed
number of X forced the same two weekdays every week, so the good pairs could
never take turns. Rule C (``constraints_consecutive``, no more than 5 working
days in a row) stays next to it.

Weeks run across month boundaries:

* the week that started last month: its days before the 1st are fixed facts
  from history (``SolverInput.previous_working``; a day with no history
  counts as not worked);
* the week that ends next month: only the days inside this month are capped
  at 5 — next month's generation judges the whole week with history.

Rest = any non-working code (X, CD, pinned leave). Soft with slack like the
other rest rules (decision #2).
"""

from __future__ import annotations

from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import OFF_CODES, codes_for
from app.scheduler.slack_registry import SlackRegistry

MAX_WORKING = 5


def weeks(days: list[date]) -> list[tuple[date, list[date], list[date]]]:
    """(Monday, days before the month, days of the month) for each Mon–Sun
    week touching ``days`` (sorted, contiguous). Shared with the re-check."""
    days = sorted(days)
    if not days:
        return []
    first_monday = days[0] - timedelta(days=days[0].weekday())
    before = [first_monday + timedelta(days=n) for n in range(days[0].weekday())]
    out: list[tuple[date, list[date], list[date]]] = []
    for day in days:
        if day.weekday() == 0 or not out:
            monday = day - timedelta(days=day.weekday())
            out.append((monday, before if not out else [], []))
        out[-1][2].append(day)
    return out


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    for person in inp.people:
        history = inp.previous_working.get(person.user_id, {})
        working_codes = [c for c in codes_for(person.role) if c not in OFF_CODES]
        for monday, before, inside in weeks(inp.days):
            if len(before) + len(inside) <= MAX_WORKING:
                continue  # cannot break the rule
            fixed = sum(1 for d in before if history.get(d, False))
            slack = model.new_int_var(
                0, 2, f"week_{person.user_id}_{monday.isoformat()}"
            )
            model.add(
                fixed
                + sum(x[(person.user_id, d, c)] for d in inside for c in working_codes)
                <= MAX_WORKING + slack
            )
            registry.register(
                slack,
                rule="weekly_max_five_working",
                message=(
                    f"User {person.user_id}: more than 5 working days in the "
                    f"week starting {monday}"
                ),
                day=monday,
                user_id=person.user_id,
                params={"start": monday},
            )
