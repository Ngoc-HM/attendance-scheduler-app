"""Sick-day A/D backfill selection (spec §6 / F-10) — pure logic, no DB.

When someone reports sick (S) on a day they held a flight shift, that shift
must be covered by a colleague taking an A/D double shift (§6). Candidate
selection, in priority order:

1. RECENTLY-SICK RULE (§6): whoever was sick earlier this month and is now
   working a single flight shift that day is FORCED to take the A/D cover
   (most recent sickness first).
2. Otherwise: the working fixed-group member with the fewest A/D doubles so
   far this month (fairness), tie-broken by user id (determinism).

Only people already on a single flight shift (A or D) that day qualify — an
A/D means covering their own shift plus the dropped one. If nobody qualifies
the admin resolves manually (F-09); the caller reports that.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.models.enums import AttendanceCode, Role

FLIGHT_SINGLE = {AttendanceCode.A, AttendanceCode.D}
FLIGHT_DUTY = {AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D}


@dataclass(frozen=True)
class BackfillProposal:
    user_id: int
    new_code: AttendanceCode  # always A/D (§6)
    forced: bool              # True when the recently-sick rule applied
    reason: str


def needs_cover(dropped_code: AttendanceCode | None) -> bool:
    """Coverage is required only when the sick person held a flight duty."""
    return dropped_code in FLIGHT_DUTY


def pick_candidate(
    sick_user_id: int,
    day_codes: dict[int, AttendanceCode],
    roles: dict[int, Role],
    recently_sick: list[int],
    month_ad_counts: dict[int, int],
) -> BackfillProposal | None:
    """Choose who takes the A/D cover for ``sick_user_id``'s dropped shift.

    ``day_codes``: that day's code per user (actuals, falling back to plan).
    ``recently_sick``: user ids with an earlier S this month, most recent
    first. ``month_ad_counts``: A/D doubles already worked this month.
    """
    candidates = [
        uid
        for uid, code in day_codes.items()
        if uid != sick_user_id
        and code in FLIGHT_SINGLE
        and roles.get(uid) is not None
        and roles[uid].is_fixed
    ]
    if not candidates:
        return None

    # 1. Recently-sick people are forced to cover (§6), most recent first.
    for uid in recently_sick:
        if uid in candidates:
            return BackfillProposal(
                user_id=uid,
                new_code=AttendanceCode.A_D,
                forced=True,
                reason="recently sick — forced A/D cover (§6)",
            )

    # 2. Fairness: fewest A/D doubles this month, then lowest id.
    chosen = min(candidates, key=lambda uid: (month_ad_counts.get(uid, 0), uid))
    return BackfillProposal(
        user_id=chosen,
        new_code=AttendanceCode.A_D,
        forced=False,
        reason="fewest A/D doubles this month",
    )
