"""Advisory conflict-ranking for competing leave requests (spec §5.4 #9, §6).

When multiple users request off on the same day the admin must decide who is
approved. This module provides a *pure, DB-free* ranking that applies the
three agreed criteria in order:

1. **Outstanding comp days** — higher ``carry_comp`` first (the caller passes
   the values ``schedule_history`` derives, never the stored column).
2. **Weekly rest entitlement** — whoever already holds FEWER approved off days
   in the 7-day block(s) the request touches ranks higher (everyone is owed
   2 days per block; the person with less of it has the stronger claim).
3. **Weekend pairing** — a span that forms Sat+Sun ranks above Fri+Sat, which
   ranks above Sun+Mon (§5.4 #8 ordering).

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


def _block_key(d: date) -> tuple[int, int, int]:
    """7-day block anchored at day 1 of the month (decision #7)."""
    return (d.year, d.month, (d.day - 1) // 7)


def offs_already_in_blocks(
    start: date, end: date, approved_off: Iterable[date]
) -> int:
    """Approved off days the user already holds in the blocks this span touches.

    The span's own days are excluded so a re-ranked, already-approved request
    does not count against itself.
    """
    own = set(_span(start, end))
    blocks = {_block_key(d) for d in own}
    return sum(
        1 for d in approved_off if d not in own and _block_key(d) in blocks
    )


def weekend_pair_score(start: date, end: date) -> int:
    """3 for a span containing Sat+Sun, 2 for Fri+Sat, 1 for Sun+Mon, else 0."""
    days = _span(start, end)
    weekdays = {d.weekday() for d in days}
    pairs = {
        (days[i].weekday(), days[i + 1].weekday()) for i in range(len(days) - 1)
    }
    if (SATURDAY, SUNDAY) in pairs:
        return 3
    if (FRIDAY, SATURDAY) in pairs:
        return 2
    if (SUNDAY, MONDAY) in pairs:
        return 1
    _ = weekdays  # single-day spans never pair
    return 0


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
        held = offs_already_in_blocks(
            req.start_date, req.end_date, approved.get(req.user_id, set())
        )
        weekend = weekend_pair_score(req.start_date, req.end_date)
        # Negate "higher is better" keys so the sort is ascending overall.
        return (-carry, held, -weekend, req.created_at, req.id)

    return sorted(requests, key=sort_key)
