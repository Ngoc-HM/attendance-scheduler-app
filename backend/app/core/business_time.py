"""Business-day clock: "what day is it?" in the operation's timezone (spec §2).

The API process may run in UTC (the Docker image sets no ``TZ``) while every
business rule — the monthly leave window, the day-after-``AUTORUN_DAY``
autorun at 00:05 — runs on Frankfurt local time (``settings.TIMEZONE``).
Around midnight the two dates differ, so business rules must call
``business_today()``, never ``date.today()``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def _utcnow() -> datetime:
    """Clock source, kept separate so tests can freeze it."""
    return datetime.now(UTC)


def business_now() -> datetime:
    """The current moment in ``settings.TIMEZONE`` (tz-aware, freezable)."""
    return _utcnow().astimezone(ZoneInfo(settings.TIMEZONE))


def business_today() -> date:
    """Today's date in ``settings.TIMEZONE`` (not the host's local zone)."""
    return business_now().date()


def local_hm(moment: datetime | None) -> str | None:
    """``moment`` as HH:MM in ``settings.TIMEZONE`` (None stays None).

    The one place an instant becomes a wall-clock time for people: the app
    shows these strings, so every screen reads the business clock whatever
    the zone of the device it runs on.
    """
    if moment is None:
        return None
    if moment.tzinfo is None:  # SQLite hands back naive UTC
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(ZoneInfo(settings.TIMEZONE)).strftime("%H:%M")
