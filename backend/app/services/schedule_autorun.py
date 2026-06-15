"""Day-20 autorun job (locked decision #9, spec F-05/F-07).

On day ``AUTORUN_DAY`` of month M the registration window for M+1 is closed
(window logic, ``leave_windows``) and a DRAFT schedule for M+1 is generated —
unless one already exists (the job NEVER clobbers a draft or published
schedule). Admins keep the manual generate button regardless.

``maybe_run_autorun`` is a pure-ish trigger (testable without APScheduler);
``start_scheduler`` wires it into a background scheduler for the app lifespan.
"""

from __future__ import annotations

import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.schedule import MonthlySchedule

logger = logging.getLogger(__name__)


def next_month(today: date) -> tuple[int, int]:
    return (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)


def maybe_run_autorun(today: date | None = None) -> bool:
    """Generate next month's draft if today is AUTORUN_DAY and none exists.

    Returns True when a generation was performed (used by tests/monitoring).
    """
    today = today or date.today()
    if not settings.AUTORUN_ENABLED or today.day != settings.AUTORUN_DAY:
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
        from app.services import schedule_service

        result = schedule_service.generate(db, year, month)
        logger.info(
            "Autorun: generated draft %s-%02d (violations: %d). Actor: system.",
            year, month, len(result.violations),
        )
        return True
    except Exception:  # job must never crash the scheduler loop
        logger.exception("Autorun: generation for %s-%02d failed.", year, month)
        return False
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler | None:
    """Start the daily check (02:00 server time). Returns None when disabled."""
    if not settings.AUTORUN_ENABLED:
        return None
    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
    scheduler.add_job(maybe_run_autorun, "cron", hour=2, minute=0, id="day20-autorun")
    scheduler.start()
    logger.info("Day-20 autorun scheduler started (day=%d).", settings.AUTORUN_DAY)
    return scheduler
