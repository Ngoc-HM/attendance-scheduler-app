"""Synthetic multi-month scheduling audit; never opens a database.

Run from backend: PYTHONPATH=. .venv/bin/python scripts/audit_scheduler.py
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import timedelta

from app.models.enums import AttendanceCode, Role
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import month_days
from app.scheduler.domain import RestTurnHistory


def main() -> None:
    history = {uid: {} for uid in range(1, 5)}
    reports = []
    for year, month in ((2027, 2), (2027, 3), (2027, 4)):
        days = month_days(year, month)
        people = []
        for uid, cells in history.items():
            turns = {}
            for kind in (4, 5, 6):
                ends = [
                    day + timedelta(days=1)
                    for day, code in cells.items()
                    if code is AttendanceCode.X
                    and day.weekday() == kind
                    and cells.get(day + timedelta(days=1)) is AttendanceCode.X
                ]
                turns[kind] = RestTurnHistory(count=len(ends), last_date=max(ends, default=None))
            previous = tuple(cells[d] for d in sorted(cells)[-6:])
            streak = 0
            for code in reversed(previous):
                if not code.is_working:
                    break
                streak += 1
            people.append(
                PersonInput(uid, Role.A, carry_streak=streak, prev_codes=previous, rest_turns=turns)
            )
        inp = SolverInput(
            year=year,
            month=month,
            people=people,
            days=days,
            flight_pairs={d: 2 if d.weekday() == 2 else 1 for d in days},
            max_solve_seconds=30,
        )
        out = SchedulerEngine(num_workers=1).solve(inp)
        rows = []
        for person in people:
            cells = {a.day: a.code for a in out.assignments if a.user_id == person.user_id}
            counts = Counter(cells.values())
            combined = history[person.user_id] | cells
            turns = {
                str(kind): sum(
                    code is AttendanceCode.X
                    and day.weekday() == kind
                    and combined.get(day + timedelta(days=1)) is AttendanceCode.X
                    and day + timedelta(days=1) in cells
                    for day, code in combined.items()
                )
                for kind in (4, 5, 6)
            }
            rows.append(
                {
                    "user": person.user_id,
                    "A": counts[AttendanceCode.A],
                    "D": counts[AttendanceCode.D],
                    "X": counts[AttendanceCode.X],
                    "gap": abs(counts[AttendanceCode.A] - counts[AttendanceCode.D]),
                    "turns": turns,
                }
            )
            history[person.user_id].update(cells)
        reports.append(
            {
                "month": f"{year}-{month:02}",
                "status": out.status,
                "violations": [v.rule for v in out.violations],
                "phases": out.phase_diagnostics,
                "people": rows,
            }
        )
    print(json.dumps(reports, indent=2, default=str))


if __name__ == "__main__":
    main()
