"""Advisory conflict-ranking for competing leave requests (spec §5.4 #9).

When multiple users request off on the same day the admin must decide who is
approved.  This module provides a *pure, DB-free* ranking function that orders
requests by descending carry_comp (outstanding compensation days), with a
stable tie-break by (created_at, id) so the result is deterministic.

The admin makes the final call; this ranking is advisory only (spec §3 fixed
group has strict review, but the engine never auto-rejects).
"""

from __future__ import annotations

from app.models.leave import LeaveRequest
from app.models.user import User


def rank(
    requests: list[LeaveRequest],
    users_by_id: dict[int, User],
) -> list[LeaveRequest]:
    """Return *requests* sorted by conflict-resolution priority (highest first).

    Priority order (spec §5.4 #9):
    1. Higher carry_comp first (more outstanding comp days → higher priority).
    2. Stable tie-break: earlier created_at, then lower id.

    Parameters
    ----------
    requests:
        All leave requests that overlap the contested date (any status).
    users_by_id:
        Mapping of user_id → User for carry_comp look-up.  Unknown users
        are treated as carry_comp=0 so the sort never crashes.
    """

    def sort_key(req: LeaveRequest) -> tuple:
        user = users_by_id.get(req.user_id)
        carry = user.carry_comp if user is not None else 0
        # Negate carry_comp so higher value sorts first.
        return (-carry, req.created_at, req.id)

    return sorted(requests, key=sort_key)
