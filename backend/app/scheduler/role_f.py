"""Group F follows the flights (customer 2026-11-18).

Group T is unchanged; F keeps the code AD and never earns or owes make-up
days. What changes for F:

* **Duty per day** (``need``): Monday–Friday, a day with two flight pairs
  needs two people and a day with one pair (or none) needs one; Saturday and
  Sunday always need one, whatever the flights. Applies to a group of two or
  more — one person alone cannot follow it.
* **Weekly rest** (``week_rest``): two ordinary X per Monday–Sunday week, so
  five working days out of seven. This replaces the monthly X count the
  other groups use. Approved leave is additional to it, except leave on a
  Saturday or Sunday, which takes the place of one rest day (the same
  adjustment the monthly count makes).
* **Turns** (``rotation_duty``): on a day that does not need everybody the
  duty goes round the group in order, and each new week starts with the next
  person, so nobody keeps the same weekdays off. With today's flights (one
  pair on Tuesday and Friday) one person works Tuesday and Saturday and rests
  Friday and Sunday, the other the reverse; the week after they swap.

A week that asks for more than five days per person keeps the five-day week:
the short day is reported (``STAFFING_WEIGHT`` is below the rest slack) and
the admin arranges cover by hand.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput
from app.scheduler.slack_registry import SLACK_WEIGHT, SlackRegistry

WEEKLY_REST = 2
MIN_GROUP = 2
# Below the rest and consecutive-day slack, above the comp-day slack.
STAFFING_WEIGHT = SLACK_WEIGHT * 6 // 10
_LEAVE = (AttendanceCode.AL, AttendanceCode.S)


def need(day: date, pairs: int, head_count: int) -> int:
    """People of group F due at work on ``day``."""
    if head_count < MIN_GROUP:
        return 0
    if day.weekday() >= 5:
        return 1
    return min(head_count, 2 if pairs >= 2 else 1)


@dataclass(frozen=True)
class WeekRest:
    """Ordinary X one person may hold in this month's part of a week."""

    monday: date
    days: list[date]  # this month's days of the week, leave days included
    low: int
    high: int
    target: int


def week_rest(
    days: list[date],
    pinned: Mapping[date, AttendanceCode] | set[date],
    prev: Mapping[date, AttendanceCode],
) -> list[WeekRest]:
    """Rest bounds per Monday–Sunday week touching ``days`` (one month).

    ``pinned`` are this month's leave days (not ordinary rest); ``prev`` the
    previous month's codes by date. A week lying fully in known days gets an
    exact count (``low == high``); a week that runs into the next month, or
    back into days without history, gets the range the missing days allow.
    """
    days = sorted(days)
    if not days:
        return []
    month = set(days)
    out: list[WeekRest] = []
    monday = days[0] - timedelta(days=days[0].weekday())
    while monday <= days[-1]:
        week = [monday + timedelta(days=n) for n in range(7)]
        current = [d for d in week if d in month]
        before = [d for d in week if d < days[0]]
        known_before = all(d in prev for d in before)
        outside = (7 - len(current) - len(before)) + (0 if known_before else len(before))
        weekend_leave = sum(d.weekday() >= 5 and d in pinned for d in current)
        rested = 0
        if known_before:
            weekend_leave += sum(d.weekday() >= 5 and prev[d] in _LEAVE for d in before)
            rested = sum(prev[d] is AttendanceCode.X for d in before)
        target = max(0, WEEKLY_REST - weekend_leave)
        free = sum(d not in pinned for d in current)
        high = min(free, max(0, target - rested))
        low = min(free, max(0, target - rested - outside))
        out.append(WeekRest(monday, current, low, high, target))
        monday += timedelta(days=7)
    return out


def previous_codes(
    first_day: date, codes: tuple[AttendanceCode, ...]
) -> dict[date, AttendanceCode]:
    """``PersonInput.prev_codes`` (oldest first, ending the day before
    ``first_day``) keyed by date."""
    return {first_day - timedelta(days=len(codes) - i): code for i, code in enumerate(codes)}


def rotation_duty(
    days: list[date],
    flight_pairs: Mapping[date, int],
    prev_flight_pairs: Mapping[date, int],
    members: list[int],
) -> dict[date, list[int]]:
    """Whose turn it is on each day of the month that needs fewer than all
    ``members`` (group F, in a fixed order).

    Within a week the turn moves on at every such day; week ``w`` starts at
    member ``w``, so the pattern shifts by one person each week. The days of
    a first week that lie in the previous month are counted too
    (``prev_flight_pairs``; a weekday without flight data counts as a full
    day), so the turn continues across the month boundary.
    """
    days = sorted(days)
    n = len(members)
    duty: dict[date, list[int]] = {}
    if n < MIN_GROUP or not days:
        return duty
    month = set(days)
    monday = days[0] - timedelta(days=days[0].weekday())
    while monday <= days[-1]:
        offset = (monday.toordinal() - 1) // 7
        for step in range(7):
            day = monday + timedelta(days=step)
            if day > days[-1]:
                break
            pairs = flight_pairs.get(day, 0) if day in month else prev_flight_pairs.get(day, 2)
            due = need(day, pairs, n)
            if due >= n:
                continue
            if day in month:
                duty[day] = [members[(offset + j) % n] for j in range(due)]
            offset += due
        monday += timedelta(days=7)
    return duty


def _members(inp: SolverInput) -> list[int]:
    return sorted(p.user_id for p in inp.people if p.role is Role.F)


def add(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    """Duty floor per day and the two-rest-days week, both with slack."""
    members = _members(inp)
    days = sorted(inp.days)
    for d in days:
        due = need(d, inp.flight_pairs.get(d, 0), len(members))
        if due == 0:
            continue
        short = model.new_int_var(0, due, f"role_f_short_{d.isoformat()}")
        model.add(sum(x[(uid, d, AttendanceCode.AD)] for uid in members) + short >= due)
        registry.register(
            short,
            rule="role_f_staffing",
            message=f"{d}: group F short (need {due})",
            day=d,
            weight=STAFFING_WEIGHT,
            params={"need": due},
        )

    for person in inp.people:
        if person.role is not Role.F:
            continue
        uid = person.user_id
        pinned = inp.approved_off.get(uid, {})
        prev = previous_codes(days[0], person.prev_codes) if days else {}
        for week in week_rest(days, pinned, prev):
            chosen = sum(x[(uid, d, AttendanceCode.X)] for d in week.days if d not in pinned)
            under = model.new_int_var(0, 7, f"role_f_rest_under_{uid}_{week.monday}")
            over = model.new_int_var(0, 7, f"role_f_rest_over_{uid}_{week.monday}")
            model.add(chosen + under >= week.low)
            model.add(chosen - over <= week.high)
            for slack, direction in ((under, "shortfall"), (over, "excess")):
                registry.register(
                    slack,
                    rule=f"role_f_weekly_off_{direction}",
                    message=(
                        f"User {uid}: weekly X {direction} in the week of "
                        f"{week.monday} (target {week.target})"
                    ),
                    day=week.monday,
                    user_id=uid,
                    params={"start": week.monday, "target": week.target},
                )


def rotation_terms(
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> list[cp_model.LinearExprT]:
    """One penalty per turn not taken: the person whose turn it is does not
    work that day. A turn that falls on the person's leave is skipped."""
    duty = rotation_duty(inp.days, inp.flight_pairs, inp.prev_flight_pairs, _members(inp))
    return [
        1 - x[(uid, d, AttendanceCode.AD)]
        for d, people in duty.items()
        for uid in people
        if d not in inp.approved_off.get(uid, {})
    ]
