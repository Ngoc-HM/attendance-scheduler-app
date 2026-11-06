"""Day-20 autorun job (locked decision #9, spec F-05/F-07).

The monthly registration window for M+1 stays open through the whole of day
``AUTORUN_DAY`` of month M (``leave_windows.registration_last_day``). Once it
has closed — at 00:05 on day ``AUTORUN_DAY + 1`` (default: day 21) — a DRAFT
schedule for M+1 is generated, so every leave registered on the last day is
included. The job skips when a schedule already exists (it NEVER clobbers a
draft or published schedule). Admins keep the manual generate button
regardless.

``maybe_run_autorun`` is a pure-ish trigger (testable without APScheduler);
``start_scheduler`` wires it into a background scheduler for the app lifespan.
"""

from __future__ import annotations

import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.business_time import business_today
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.schedule import MonthlySchedule

logger = logging.getLogger(__name__)


def next_month(today: date) -> tuple[int, int]:
    return (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)


def maybe_run_autorun(today: date | None = None) -> bool:
    """Generate next month's draft the day after AUTORUN_DAY if none exists.

    Day ``AUTORUN_DAY`` is still inside the registration window, so the run
    waits until ``AUTORUN_DAY + 1``. ``today`` defaults to the business date in
    ``TIMEZONE`` — the cron fires at 00:05 Berlin, when a UTC host still reads
    the previous day. Returns True when a generation was performed (used by
    tests/monitoring).
    """
    today = today or business_today()
    if not settings.AUTORUN_ENABLED or today.day != settings.AUTORUN_DAY + 1:
        return False

    year, month = next_month(today)
    db = SessionLocal()
    try:
        exists = (
            db.query(MonthlySchedule)
            .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
            .one_or_none()
        )
        if exists is not None:
            logger.info("Autorun: schedule %s-%02d already exists, skipping.", year, month)
            return False

        # Import here to avoid a service-module import cycle.
        from app.services import audit_service, schedule_service

        result = schedule_service.generate(db, year, month)
        logger.info(
            "Autorun: generated draft %s-%02d (violations: %d). Actor: system.",
            year, month, len(result.violations),
        )
        # System actor (actor_id=None) — the trail must show automated runs too.
        audit_service.record(
            db, None, "schedule.generate", "MonthlySchedule",
            detail=f"{year}-{month:02d} autorun violations={len(result.violations)}",
        )
        return True
    except Exception:  # job must never crash the scheduler loop
        logger.exception("Autorun: generation for %s-%02d failed.", year, month)
        return False
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler | None:
    """Start the daily check (00:05 in ``TIMEZONE``). Returns None when disabled.

    00:05 is just after midnight, so on day ``AUTORUN_DAY + 1`` the run sees
    the registration window already closed.
    """
    if not settings.AUTORUN_ENABLED:
        return None
    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
    scheduler.add_job(maybe_run_autorun, "cron", hour=0, minute=5, id="day20-autorun")
    scheduler.start()
    logger.info(
        "Autorun scheduler started (window closes after day %d; draft at 00:05 on day %d).",
        settings.AUTORUN_DAY, settings.AUTORUN_DAY + 1,
    )
    return scheduler
