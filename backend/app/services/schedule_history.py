"""Effective scheduling history used when building a new month.

Actual attendance wins over the planned schedule for the same user/day.  When
an actual row is still missing (normal while next month's draft is generated),
the planned assignment is the best available fact.  This lets the next month
honour compensation (A/D, and holiday work for every role) and month-boundary
rest rules without requiring a manual "close month" step first. The same
history gives the good-pair carry (``carry_pair_points``, owner 2026-11-12).
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import ColumnElement, and_, case, exists, extract, false, func, or_, select, true
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.core.config import settings
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode
from app.models.holiday import Holiday
from app.models.schedule import ShiftAssignment
from app.models.user import User
from app.services.carry_over_math import comp_balance_from_counts, pair_points

# Days read back from the cutoff for the streak, the weekly-rest flags and
# the off-chain codes. Every rule that crosses the month boundary looks at
# most six days back, so a longer working run is reported as 6 ("6 or more").
BOUNDARY_DAYS = 6

_WORKING_CODES = [c for c in AttendanceCode if c.is_working]
_SUNDAY, _SATURDAY = 0, 6  # SQL day-of-week numbering (SQLite %w, PostgreSQL dow)


@dataclass(frozen=True)
class BoundaryState:
    carry_comp: int
    carry_streak: int
    # Worked or not, each of the six days before the month (no cell = not
    # worked): the Mon–Sun week that started last month (weekly rest rule).
    previous_working: dict[date, bool]
    # Premium offs (X on Sat/Sun/holiday) received so far — derived from the
    # effective history like comp/streak, so no month-close step is needed
    # before the fairness objective (decision #6) can rotate the perk.
    carry_premium_off: int = 0
    # Effective codes of the previous month's last days, oldest first: at most
    # BOUNDARY_DAYS, ending on its last day, cut short at a day with no cell,
    # empty without history. Read by the off-chain rule (engine and checker).
    prev_codes: tuple[AttendanceCode, ...] = ()


@dataclass
class _Counts:
    """History aggregates for one user (``carry_over_math`` inputs)."""

    cells: int = 0
    earned_before: int = 0
    consumed_before: int = 0
    earned_from: int = 0
    consumed_from: int = 0
    premium_off: int = 0


def previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _aggregate(
    db: Session,
    into: dict[int, _Counts],
    user_col: InstrumentedAttribute[int],
    date_col: InstrumentedAttribute[date],
    code_col: InstrumentedAttribute[AttendanceCode],
    *where: ColumnElement[bool],
) -> None:
    """Add one source's per-user comp/premium counts, computed in SQL."""
    effective_from = settings.HOLIDAY_COMP_EFFECTIVE_FROM
    from_date: ColumnElement[bool] = (
        date_col >= effective_from if effective_from is not None else true()
    )
    before_date: ColumnElement[bool] = (
        date_col < effective_from if effective_from is not None else false()
    )
    holiday = date_col.in_(select(Holiday.day))
    weekend = extract("dow", date_col).in_((_SUNDAY, _SATURDAY))

    def count(condition: ColumnElement[bool]) -> ColumnElement[int]:
        return func.sum(case((condition, 1), else_=0))

    stmt = (
        select(
            user_col,
            func.count(),
            count(and_(before_date, code_col == AttendanceCode.A_D)),
            count(and_(before_date, code_col == AttendanceCode.CD)),
            count(and_(from_date, code_col == AttendanceCode.A_D))
            + count(and_(from_date, holiday, code_col.in_(_WORKING_CODES))),
            count(and_(from_date, code_col == AttendanceCode.CD)),
            count(and_(code_col == AttendanceCode.X, or_(weekend, holiday))),
        )
        .where(*where)
        .group_by(user_col)
    )
    for uid, cells, eb, cb, ef, cf, prem in db.execute(stmt):
        c = into.setdefault(uid, _Counts())
        c.cells += int(cells)
        c.earned_before += int(eb or 0)
        c.consumed_before += int(cb or 0)
        c.earned_from += int(ef or 0)
        c.consumed_from += int(cf or 0)
        c.premium_off += int(prem or 0)


def _history_counts(db: Session, user_ids: set[int], cutoff: date) -> dict[int, _Counts]:
    """Comp/premium aggregates over the effective history up to ``cutoff``.

    Effective history = actual attendance, plus planned cells that have no
    actual row (actual wins over the plan for the same user/day).
    """
    counts: dict[int, _Counts] = {}
    AR, SA = AttendanceRecord, ShiftAssignment
    _aggregate(
        db, counts, AR.user_id, AR.work_date, AR.code,
        AR.user_id.in_(user_ids), AR.work_date <= cutoff,
    )
    has_actual = exists().where(AR.user_id == SA.user_id, AR.work_date == SA.work_date)
    _aggregate(
        db, counts, SA.user_id, SA.work_date, SA.code,
        SA.user_id.in_(user_ids), SA.work_date <= cutoff, ~has_actual,
    )
    return counts


def _boundary_grid(
    db: Session, user_ids: set[int], cutoff: date
) -> dict[tuple[int, date], AttendanceCode]:
    """Effective codes of the last BOUNDARY_DAYS days up to ``cutoff``."""
    first = cutoff - timedelta(days=BOUNDARY_DAYS - 1)
    grid: dict[tuple[int, date], AttendanceCode] = {}
    # Planned first, actual on top.
    for model in (ShiftAssignment, AttendanceRecord):
        rows = db.execute(
            select(model.user_id, model.work_date, model.code).where(
                model.user_id.in_(user_ids),
                model.work_date >= first,
                model.work_date <= cutoff,
            )
        )
        for uid, day, code in rows:
            grid[(uid, day)] = code
    return grid


def carry_pair_points(
    db: Session, user_ids: set[int], target_year: int, target_month: int
) -> dict[int, int]:
    """Weekday-bonus points of each user's X+X pairs in the effective history
    of the 12 months before ``target_year/target_month`` (0 without history).

    Two statements for the whole group: the actual X cells, then the planned
    X cells of days with no actual row (actual wins over the plan, like
    comp/premium). Only genuine X is read, so AL/CD/S never form a pair; the
    pairs are counted in Python (``carry_over_math.pair_points``).
    """
    if not user_ids:
        return {}
    first = date(target_year - 1, target_month, 1)
    cutoff = date(target_year, target_month, 1) - timedelta(days=1)
    AR, SA = AttendanceRecord, ShiftAssignment
    has_actual = exists().where(AR.user_id == SA.user_id, AR.work_date == SA.work_date)
    actual = select(AR.user_id, AR.work_date).where(
        AR.user_id.in_(user_ids), AR.work_date >= first, AR.work_date <= cutoff,
        AR.code == AttendanceCode.X,
    )
    planned = select(SA.user_id, SA.work_date).where(
        SA.user_id.in_(user_ids), SA.work_date >= first, SA.work_date <= cutoff,
        SA.code == AttendanceCode.X, ~has_actual,
    )
    offs: dict[int, set[date]] = {}
    for stmt in (actual, planned):
        for uid, day in db.execute(stmt):
            offs.setdefault(uid, set()).add(day)
    return {uid: pair_points(offs.get(uid, ())) for uid in user_ids}


def build_boundary_states(
    db: Session, users: list[User], target_year: int, target_month: int
) -> dict[int, BoundaryState]:
    """Derive carry values immediately before ``target_year/target_month``.

    A fixed number of statements whatever the number of users (F14): comp
    and premium counts are aggregated in SQL; only the last six days are read
    row by row, for the streak, the working flags and ``prev_codes``.
    """
    prev_year, prev_month = previous_month(target_year, target_month)
    cutoff = date(prev_year, prev_month, calendar.monthrange(prev_year, prev_month)[1])
    user_ids = {u.id for u in users}
    if not user_ids:
        return {}
    counts = _history_counts(db, user_ids, cutoff)
    grid = _boundary_grid(db, user_ids, cutoff)
    window = [cutoff - timedelta(days=offset) for offset in range(BOUNDARY_DAYS - 1, -1, -1)]

    states: dict[int, BoundaryState] = {}
    for user in users:
        # A user appears in the aggregates only with at least one cell.
        history = counts.get(user.id)
        has_history = history is not None

        # Every role earns compensation (A/D, or working a public holiday from
        # HOLIDAY_COMP_EFFECTIVE_FROM on) and consumes it with CD.  Stored carry
        # is a fallback for legacy databases where old rows are absent.
        if history is not None:
            carry_comp = comp_balance_from_counts(
                history.earned_before,
                history.consumed_before,
                history.earned_from,
                history.consumed_from,
            )
            # Premium-off fairness input (decision #6), same history-first rule.
            carry_premium_off = history.premium_off
        else:
            carry_comp = user.carry_comp
            carry_premium_off = user.carry_premium_off

        # The known codes of a contiguous run of days ending on the cutoff.
        trailing: list[AttendanceCode] = []
        for day in reversed(window):
            code = grid.get((user.id, day))
            if code is None:
                break
            trailing.append(code)
        prev_codes = tuple(reversed(trailing))

        # Count a genuinely contiguous run ending on the previous month's last
        # calendar day. Only a user with NO history at all falls back to the
        # legacy stored scalar; with history, a missing cell (e.g. on the
        # cutoff day) is an unknown day treated as rest, so it breaks the run.
        # Never reading the stored value back for such users keeps month-close
        # from re-writing a stale streak forever.
        carry_streak = 0
        if not has_history:
            carry_streak = max(0, user.carry_streak)
        else:
            for code in trailing:
                if not code.is_working:
                    break
                carry_streak += 1

        previous_working: dict[date, bool] = {}
        streak_start = cutoff - timedelta(days=max(0, carry_streak - 1))
        for day in window:
            code = grid.get((user.id, day))
            if code is not None:
                previous_working[day] = code.is_working
            else:
                # The no-history fallback reconstructs the stored trailing work
                # run; any other unknown day is rest rather than invented work.
                previous_working[day] = carry_streak > 0 and day >= streak_start

        states[user.id] = BoundaryState(
            carry_comp=carry_comp,
            carry_streak=carry_streak,
            previous_working=previous_working,
            carry_premium_off=carry_premium_off,
            prev_codes=prev_codes,
        )
    return states
