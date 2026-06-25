"""Hard-rule re-check after manual edits (F-09) and shift-change applies (#8).

Pure functions over a plain ``{(user_id, date): AttendanceCode}`` grid — no DB,
no solver — mirroring the engine's soft rules (§5.3 #2/#3/#4). The edit is
ALWAYS saved (§5.6 #14: the admin confirms violations, the system never
silently blocks); these warnings tell the admin what just broke.
"""

from __future__ import annotations

from datetime import date

from app.models.enums import AttendanceCode, Role
from app.scheduler.calendar_utils import partial_block_off_target

# Demand table per flight_pairs (§5.3 #4) — kept in sync with the engine.
DEMAND: dict[int, tuple[int, int]] = {0: (0, 0), 1: (1, 1), 2: (1, 2)}

# Codes that count as a day off for the consecutive-run rule (§5.2).
OFF_CODES = {AttendanceCode.X, AttendanceCode.CD, AttendanceCode.S, AttendanceCode.AL}


def recheck(
    grid: dict[tuple[int, date], AttendanceCode],
    roles: dict[int, Role],
    carry_streaks: dict[int, int],
    weeks: list[list[date]],
    flight_pairs: dict[date, int],
) -> list[str]:
    """Run every §5.3 check over the grid; return human-readable warnings."""
    warnings: list[str] = []
    warnings += check_consecutive(grid, roles, carry_streaks, weeks)
    warnings += check_off_quota(grid, roles, weeks)
    warnings += check_staffing(grid, roles, weeks, flight_pairs)
    return warnings


def check_consecutive(grid, roles, carry_streaks, weeks) -> list[str]:
    """§5.3 #3 + §5.5 — no run of more than 5 working days (carry included)."""
    days = sorted({d for block in weeks for d in block})
    warnings: list[str] = []
    for uid in roles:
        run = carry_streaks.get(uid, 0)
        for d in days:
            code = grid.get((uid, d))
            if code is None or code in OFF_CODES:
                run = 0
                continue
            run += 1
            if run == 6:  # report once per streak, at the breaching day
                warnings.append(
                    f"User {uid}: more than 5 consecutive working days at {d}"
                )
        # (runs crossing into next month are next month's carry_streak)
    return warnings


def check_off_quota(grid, roles, weeks) -> list[str]:
    """§5.3 #2 — genuine X per 7-day block must meet the pro-rated target.

    AL/CD/S days do not consume the quota (decision #4) — only X counts.
    """
    warnings: list[str] = []
    for uid in roles:
        for block in weeks:
            target = partial_block_off_target(len(block))
            got = sum(1 for d in block if grid.get((uid, d)) is AttendanceCode.X)
            if got != target:
                warnings.append(
                    f"User {uid}: {got} off day(s) instead of {target} "
                    f"in block starting {block[0]}"
                )
    return warnings


def check_staffing(grid, roles, weeks, flight_pairs) -> list[str]:
    """§5.3 #4 — daily A/D coverage must meet at least the per-pairs minimum.

    A floor, not an exact match (every role takes flight duty now; O/D is no
    longer auto-assigned), and counted across ALL people — kept in sync with
    ``constraints_staffing``. Only UNDER-coverage warns; extra A/D is fine.
    """
    days = sorted({d for block in weeks for d in block})
    everyone = list(roles)
    warnings: list[str] = []
    for d in days:
        need_a, need_d = DEMAND.get(flight_pairs.get(d, 0), (0, 0))
        a = sum(1 for u in everyone if grid.get((u, d)) is AttendanceCode.A)
        dd = sum(1 for u in everyone if grid.get((u, d)) is AttendanceCode.D)
        ad = sum(1 for u in everyone if grid.get((u, d)) is AttendanceCode.A_D)
        if a + ad < need_a or dd + ad < need_d:
            warnings.append(
                f"{d}: short flight coverage A={a + ad}/{need_a}, "
                f"D={dd + ad}/{need_d} (need at least the flight minimum)"
            )
    return warnings
