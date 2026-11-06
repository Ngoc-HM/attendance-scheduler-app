"""Compliance schemas (§9.3 retention, §9.5 data-subject rights)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class RetentionPurgeRequest(BaseModel):
    """Delete personnel records strictly BEFORE ``before``.

    ``None`` → today minus ``DATA_RETENTION_MONTHS``. The cutoff can never be
    more recent than ``DATA_RETENTION_MIN_MONTHS`` ago (ArbZG §16).
    """

    before: date | None = None


class RetentionPurgeResult(BaseModel):
    cutoff: date
    deleted: dict[str, int]
