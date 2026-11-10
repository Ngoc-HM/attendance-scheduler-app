"""Admin navigation badge counts (owner 2026-11-10)."""

from __future__ import annotations

from pydantic import BaseModel


class PendingCounts(BaseModel):
    """Items waiting for an admin decision, one number per navigation tab."""

    leaves: int
    shift_changes: int
    users: int
