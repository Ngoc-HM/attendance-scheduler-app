"""Advisory conflict-ranking for competing leave requests (spec §5.4 #9, §6).

When multiple users request off on the same day the admin must decide who is
approved. This module provides a *pure, DB-free* ranking that applies the
three agreed criteria in order:

1. **Outstanding comp days** — higher ``carry_comp`` first (the caller passes
   the values ``schedule_history`` derives, never the stored column).
2. **Rest entitlement** — whoever already holds FEWER approved off days in
   the rolling 7-day windows the request touches ranks higher: the six days
   before and after the span (owner 2026-11-10 — the fixed 7-day blocks are
   gone; every 7 consecutive days owe 2 rest days, so the person with less
   rest around the contested days has the stronger claim).
3. **Weekend pairing** — a span that forms Fri+Sat ranks above Sat+Sun, which
   ranks above Sun+Mon (owner 2026-11-10, the engine's pair order).

Then a stable tie-break by (created_at, id) so the result is deterministic.
The admin makes the final call; this ranking is advisory only (spec §3 fixed
group has strict review, but the engine never auto-rejects).
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from app.models.leave import LeaveRequest

FRIDAY, SATURDAY, SUNDAY, MONDAY = 4, 5, 6, 0


def _span(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


# A 7-day window holding any day of the span reaches this far either side.
AROUND_DAYS = 6


def offs_already_around(
    start: date, end: date, approved_off: Iterable[date]
) -> int:
    """Approved off days the user already holds in the 7-day windows the
    span touches, i.e. within six days before ``start`` or after ``end``.

    The span's own days are excluded so a re-ranked, already-approved request
    does not count against itself.
    """
    lo = start - timedelta(days=AROUND_DAYS)
    hi = end + timedelta(days=AROUND_DAYS)
    own = set(_span(start, end))
    return sum(1 for d in approved_off if d not in own and lo <= d <= hi)


def weekend_pair_score(start: date, end: date) -> int:
    """3 for a span containing Fri+Sat, 2 for Sat+Sun, 1 for Sun+Mon, else 0."""
    days = _span(start, end)
    pairs = {
        (days[i].weekday(), days[i + 1].weekday()) for i in range(len(days) - 1)
    }
    if (FRIDAY, SATURDAY) in pairs:
        return 3
    if (SATURDAY, SUNDAY) in pairs:
        return 2
    if (SUNDAY, MONDAY) in pairs:
        return 1
    return 0  # single-day spans never pair


def rank(
    requests: list[LeaveRequest],
    carry_comp_by_user: dict[int, int],
    approved_off_by_user: dict[int, set[date]] | None = None,
) -> list[LeaveRequest]:
    """Return *requests* sorted by conflict-resolution priority (highest first).

    Parameters
    ----------
    requests:
        All leave requests that overlap the contested date (any status).
    carry_comp_by_user:
        Outstanding comp days per user_id, as derived by ``schedule_history``
        (the same values the scheduler uses). Unknown users are treated as
        carry_comp=0 so the sort never crashes.
    approved_off_by_user:
        Already-approved off days per user (criterion 2). Missing → 0.
    """
    approved = approved_off_by_user or {}

    def sort_key(req: LeaveRequest) -> tuple:
        carry = carry_comp_by_user.get(req.user_id, 0)
        held = offs_already_around(
            req.start_date, req.end_date, approved.get(req.user_id, set())
        )
        weekend = weekend_pair_score(req.start_date, req.end_date)
        # Negate "higher is better" keys so the sort is ascending overall.
        return (-carry, held, -weekend, req.created_at, req.id)

    return sorted(requests, key=sort_key)
