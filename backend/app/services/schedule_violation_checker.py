"""Hard-rule re-check after manual edits (F-09) and shift-change applies (#8).

Pure functions over a plain ``{(user_id, date): AttendanceCode}`` grid — no DB,
no solver — mirroring EVERY rule the engine models with slack (§5.3 and the
owner decisions layered on top). The edit is saved after role/code validation
(§5.6 #14); these warnings tell the admin which scheduling rules the edit
just broke.

Rules mirrored (engine module in brackets):

* max 5 consecutive working days, carry included   [constraints_consecutive]
* >= 2 rest days in every rolling 7 days           [constraints_rolling_rest]
* genuine-X quota per full 7-day block             [constraints_off_days]
* flight staffing floor for role A                 [constraints_staffing]
* >= 2 pure A days per role-A person / full month  [constraints_role_a_distribution]
* owed comp days (CD) granted, none unearned       [constraints_comp_days]
* no more than 5 consecutive OFF days              [constraints_off_chain]

Each breach is a ``Violation`` with the engine's rule name, ``key`` and
``params`` (no prose for the client): ``schedule_violation_text`` renders it
in the request's language, so a rule reads the same after Generate and here.
``message`` is an English line for logs and tests only.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.models.enums import AttendanceCode, Role
from app.scheduler.calendar_utils import block_off_target
from app.scheduler.constraints_role_a_distribution import (
    MIN_A_DAYS,
    MIN_FULL_MONTH_DAYS,
)
from app.scheduler.domain import Violation

# Demand table per flight_pairs (§5.3 #4) — kept in sync with the engine.
DEMAND: dict[int, tuple[int, int]] = {0: (0, 0), 1: (1, 1), 2: (1, 2)}

# Codes that count as a day off for the consecutive-run rules (§5.2).
OFF_CODES = {AttendanceCode.X, AttendanceCode.CD, AttendanceCode.S, AttendanceCode.AL}

# Longest ordinary off-run allowed; a longer break must be annual leave.
MAX_CONSECUTIVE_OFF = 5


def recheck(
    grid: dict[tuple[int, date], AttendanceCode],
    roles: dict[int, Role],
    carry_streaks: dict[int, int],
    weeks: list[list[date]],
    flight_pairs: dict[date, int],
    previous_working: dict[int, dict[date, bool]] | None = None,
    carry_comps: dict[int, int] | None = None,
    annual_off: dict[int, set[date]] | None = None,
    prev_codes: dict[int, tuple[AttendanceCode, ...]] | None = None,
    cover_roles: dict[int, Role] | None = None,
) -> list[Violation]:
    """Run every mirrored rule over the grid; return one Violation per breach.

    ``prev_codes`` holds each user's previous-month codes, oldest first
    (``BoundaryState.prev_codes``), for off-runs crossing the month start.
    ``cover_roles`` are extra users whose grid cells count towards flight
    staffing only (no per-person rule) — e.g. the days a since-disabled user
    really worked.
    """
    warnings: list[Violation] = []
    warnings += check_consecutive(grid, roles, carry_streaks, weeks)
    warnings += check_rolling_rest(grid, roles, weeks, previous_working or {})
    warnings += check_off_quota(grid, roles, weeks)
    warnings += check_staffing(grid, {**(cover_roles or {}), **roles}, weeks, flight_pairs)
    warnings += check_min_a_days(grid, roles, weeks)
    warnings += check_comp_days(grid, roles, weeks, carry_comps or {})
    warnings += check_off_chain(grid, roles, weeks, annual_off or {}, prev_codes)
    return warnings


def _days(weeks: list[list[date]]) -> list[date]:
    return sorted({d for block in weeks for d in block})


def check_rolling_rest(grid, roles, weeks, previous_working) -> list[Violation]:
    """Every rolling 7 calendar days must contain at least 2 rest days."""
    days = _days(weeks)
    if not days:
        return []

    previous_days = [days[0] - timedelta(days=n) for n in range(6, 0, -1)]
    warnings: list[Violation] = []
    for uid in roles:
        historical = previous_working.get(uid, {})
        timeline = [
            (day, historical.get(day, False)) for day in previous_days
        ] + [
            (
                day,
                bool(
                    (code := grid.get((uid, day))) is not None
                    and code.is_working
                ),
            )
            for day in days
        ]
        for start in range(len(timeline) - 6):
            window = timeline[start : start + 7]
            if sum(working for _, working in window) > 5:
                warnings.append(
                    Violation(
                        rule="rolling_seven_min_two_rest",
                        message=(
                            f"User {uid}: fewer than 2 rest days in the 7-day "
                            f"window starting {window[0][0]}"
                        ),
                        day=window[0][0],
                        user_id=uid,
                        params={"start": window[0][0]},
                    )
                )
    return warnings


def check_consecutive(grid, roles, carry_streaks, weeks) -> list[Violation]:
    """§5.3 #3 + §5.5 — no run of more than 5 working days (carry included)."""
    days = _days(weeks)
    warnings: list[Violation] = []
    for uid in roles:
        # Role F is T-like (owner 2026-07-22): the consecutive rule applies.
        run = carry_streaks.get(uid, 0)
        reported = False
        for d in days:
            code = grid.get((uid, d))
            if code is None or code in OFF_CODES:
                run = 0
                reported = False
                continue
            run += 1
            # ``>=``: a carried run may already be 6 or more on day 1 (F7).
            # Report once per run, at the first breaching day.
            if run >= 6 and not reported:
                reported = True
                # The 6-day all-working window ending here (the engine's
                # window start; before day 1 when a carried run breaches).
                start = d - timedelta(days=5)
                warnings.append(
                    Violation(
                        rule="max_consecutive_working",
                        message=f"User {uid}: more than 5 consecutive working days at {d}",
                        day=start,
                        user_id=uid,
                        params={"start": start},
                    )
                )
        # (runs crossing into next month are next month's carry_streak)
    return warnings


# Leave/sick codes that occupy block days without consuming the genuine-X
# quota (decision #4) AND shrink the block's X target: the engine's pins
# (approved leave) and sick days, which nobody chooses. A CD does not consume
# the quota either, but it is placed by choice, so like in the engine it does
# not shrink the target — it competes with the weekly X.
TARGET_CAP_CODES = {AttendanceCode.AL, AttendanceCode.S}


def check_off_quota(grid, roles, weeks) -> list[Violation]:
    """§5.3 #2 — genuine X per full 7-day block must equal its target (2).

    The leftover days after the 28th (a partial block) carry no quota and are
    not checked (owner 2026-11-10) — the rest rules cover them, as in the
    engine (``calendar_utils.block_off_target``).

    AL/CD/S days do not consume the quota (decision #4) — only X counts.
    The target shrinks when leave fills the block (mirrors the engine's cap,
    2026-07-17): a person on a 6-day leave has only 1 day left for genuine X.
    Like the engine, only AL (and S) shrink it: 6 AL + 1 CD in a block still
    misses its one weekly X.
    """
    warnings: list[Violation] = []
    for uid in roles:
        for block in weeks:
            base = block_off_target(len(block))
            if base is None:
                continue  # leftover days: no quota (owner 2026-11-10)
            leave_days = sum(
                1 for d in block if grid.get((uid, d)) in TARGET_CAP_CODES
            )
            target = min(base, len(block) - leave_days)
            got = sum(1 for d in block if grid.get((uid, d)) is AttendanceCode.X)
            if got != target:
                warnings.append(
                    Violation(
                        rule="two_days_off_per_week",
                        message=(
                            f"User {uid}: {got} off day(s) instead of {target} "
                            f"in block starting {block[0]}"
                        ),
                        day=block[0],
                        user_id=uid,
                        key=(
                            "two_days_off_per_week_under"
                            if got < target
                            else "two_days_off_per_week_over"
                        ),
                        params={
                            "start": block[0],
                            "required": target,
                            "amount": abs(target - got),
                        },
                    )
                )
    return warnings


def check_staffing(grid, roles, weeks, flight_pairs) -> list[Violation]:
    """§5.3 #4 — daily A/D coverage must meet at least the per-pairs minimum.

    Scoped to ROLE-A people only (owner decision 2026-06-26), kept in sync
    with ``constraints_staffing``.  Only UNDER-coverage warns; extra is fine.
    """
    days = _days(weeks)
    role_a_ids = [uid for uid, role in roles.items() if role is Role.A]
    warnings: list[Violation] = []
    for d in days:
        need_a, need_d = DEMAND.get(flight_pairs.get(d, 0), (0, 0))
        a = sum(1 for u in role_a_ids if grid.get((u, d)) is AttendanceCode.A)
        dd = sum(1 for u in role_a_ids if grid.get((u, d)) is AttendanceCode.D)
        ad = sum(1 for u in role_a_ids if grid.get((u, d)) is AttendanceCode.A_D)
        if not (a + ad < need_a or dd + ad < need_d):
            continue
        message = (
            f"{d}: short flight coverage A={a + ad}/{need_a}, "
            f"D={dd + ad}/{need_d} (need at least the flight minimum)"
        )
        if not role_a_ids:
            # Nobody can cover: one line per day, like the engine.
            warnings.append(
                Violation(
                    rule="flight_staffing",
                    message=message,
                    day=d,
                    key="flight_staffing_no_role_a",
                    params={"need_a": need_a, "need_d": need_d},
                )
            )
            continue
        # One line per short shift, like the engine.
        for shift, have, need in (("A", a + ad, need_a), ("D", dd + ad, need_d)):
            if have < need:
                warnings.append(
                    Violation(
                        rule="flight_staffing",
                        message=message,
                        day=d,
                        params={"shift": shift, "need": need, "amount": need - have},
                    )
                )
    return warnings


def check_min_a_days(grid, roles, weeks) -> list[Violation]:
    """Decision #14 — every role-A person keeps >= 2 pure A days in a full month.

    Mirrors ``constraints_role_a_distribution``: partial-month grids (tests,
    diagnostics) are exempt exactly like in the engine.
    """
    days = _days(weeks)
    if len(days) < MIN_FULL_MONTH_DAYS:
        return []
    warnings: list[Violation] = []
    for uid, role in roles.items():
        if role is not Role.A:
            continue
        pure_a = sum(1 for d in days if grid.get((uid, d)) is AttendanceCode.A)
        if pure_a < MIN_A_DAYS:
            warnings.append(
                Violation(
                    rule="role_a_minimum_a_days",
                    message=(
                        f"User {uid}: only {pure_a} A-duty day(s) in the month "
                        f"(minimum {MIN_A_DAYS})"
                    ),
                    user_id=uid,
                    params={"minimum": MIN_A_DAYS},
                )
            )
    return warnings


def check_comp_days(grid, roles, weeks, carry_comps) -> list[Violation]:
    """§5.3 #6 / decision #13 — owed comp days are granted, none invented.

    Mirrors ``constraints_comp_days``: for every person, whatever the role
    (holiday work earns CD for all roles — owner D1 2026-11-06), the month's
    CD count must equal the comp debt carried in; fewer is a shortfall, more
    is an unearned rest day.
    """
    days = _days(weeks)
    warnings: list[Violation] = []
    for uid in roles:
        cd = sum(1 for d in days if grid.get((uid, d)) is AttendanceCode.CD)
        owed = carry_comps.get(uid, 0)
        if cd < owed:
            warnings.append(
                Violation(
                    rule="comp_day_shortfall",
                    message=f"User {uid}: {owed} comp day(s) owed but only {cd} scheduled",
                    user_id=uid,
                    params={"owed": owed, "amount": owed - cd},
                )
            )
        elif cd > owed:
            warnings.append(
                Violation(
                    rule="comp_day_excess",
                    message=f"User {uid}: {cd} comp day(s) scheduled but only {owed} owed",
                    user_id=uid,
                    params={"owed": owed, "amount": cd - owed},
                )
            )
    return warnings


def check_off_chain(grid, roles, weeks, annual_off, prev_codes=None) -> list[Violation]:
    """Customer rule 2026-06-12 — no more than 5 consecutive OFF days.

    Mirrors ``constraints_off_chain``: any 6-day window that is entirely off
    warns, unless it holds approved leave — an AL cell, an approved
    annual-leave day, or an AL among the previous month's codes (ruling R1).
    Windows reach back into the previous month through ``prev_codes``
    (oldest first, ending on its last day). Reported once per off-run, at its
    first non-exempt all-off window.
    """
    days = _days(weeks)
    if not days:
        return []
    window = MAX_CONSECUTIVE_OFF + 1
    prev_codes = prev_codes or {}
    warnings: list[Violation] = []
    for uid in roles:
        annual = annual_off.get(uid, set())
        prev = list(prev_codes.get(uid, ()))[-(window - 1) :]
        timeline = [
            (days[0] - timedelta(days=len(prev) - i), code) for i, code in enumerate(prev)
        ] + [(d, grid.get((uid, d))) for d in days]

        run_start: int | None = None
        reported = False
        for i, (_, code) in enumerate(timeline):
            if code not in OFF_CODES:
                run_start, reported = None, False
                continue
            if run_start is None:
                run_start = i
            start = i - window + 1
            if reported or start < run_start:
                continue  # already reported, or the window is not all off
            span = timeline[start : i + 1]
            if any(c is AttendanceCode.AL or d in annual for d, c in span):
                continue  # holds approved leave (R1)
            reported = True
            start_day = span[0][0]
            warnings.append(
                Violation(
                    rule="max_consecutive_off",
                    message=(
                        f"User {uid}: more than {MAX_CONSECUTIVE_OFF} consecutive "
                        f"OFF days from {start_day} — such a break must be "
                        f"registered as annual leave"
                    ),
                    day=start_day,
                    user_id=uid,
                    params={"start": start_day},
                )
            )
    return warnings
