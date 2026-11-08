"""Autorun job (locked decision #9, spec F-05/F-07).

The monthly registration window for M+1 stays open through the whole of day
``AUTORUN_DAY`` of month M (``leave_windows.registration_last_day``). Once it
has closed — at 00:05 on day ``AUTORUN_DAY + 1`` (default: day 21) — a DRAFT
schedule for M+1 is generated, so every leave registered on the last day is
included. The job skips when a schedule already exists (it NEVER clobbers a
draft or published schedule). Admins keep the manual generate button
regardless.

Catch-up (review C4): a host that was off at 00:05 must not lose the month.
The check runs on ANY day after ``AUTORUN_DAY`` while M+1 has no schedule;
the daily job tolerates a wake-up up to an hour late, and the app runs the
check once at startup. Failures are logged as errors; a next month without
flight data is logged as a warning (the draft is planned without flights).

``maybe_run_autorun`` is a pure-ish trigger (testable without APScheduler);
``start_scheduler`` wires it into a background scheduler for the app lifespan.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.business_time import business_today
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.flight import FlightDay
from app.models.schedule import MonthlySchedule

logger = logging.getLogger(__name__)

# A daily run that fires up to this late (host asleep at 00:05) still runs.
MISFIRE_GRACE_SECONDS = 3600


def next_month(today: date) -> tuple[int, int]:
    return (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    """First day of the month and first day of the following month."""
    ny, nm = next_month(date(year, month, 1))
    return date(year, month, 1), date(ny, nm, 1)


def maybe_run_autorun(today: date | None = None) -> bool:
    """Generate next month's draft once the window has closed, if none exists.

    Day ``AUTORUN_DAY`` is still inside the registration window, so the run
    waits until ``AUTORUN_DAY + 1`` — and keeps trying on every later day of
    the month while next month has no schedule (catch-up after downtime).
    ``today`` defaults to the business date in ``TIMEZONE`` — the cron fires at
    00:05 in ``TIMEZONE``, when a UTC host still reads the previous day.
    Returns True when a draft was generated (used by tests/monitoring).
    """
    today = today or business_today()
    if not settings.AUTORUN_ENABLED or today.day <= settings.AUTORUN_DAY:
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

        first, after = _month_bounds(year, month)
        has_flights = (
            db.query(FlightDay.id)
            .filter(FlightDay.day >= first, FlightDay.day < after)
            .first()
            is not None
        )
        if not has_flights:
            logger.warning(
                "Autorun: no flight days entered for %s-%02d; the draft is planned "
                "without flights. Enter the flights and regenerate.",
                year, month,
            )

        # Import here to avoid a service-module import cycle.
        from app.services import audit_service, schedule_service

        result = schedule_service.generate(db, year, month)
        if not result.feasible:
            logger.error(
                "Autorun: no feasible schedule for %s-%02d (violations: %d); nothing "
                "saved. Generate it manually; the next daily check retries.",
                year, month, len(result.violations),
            )
            return False
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


def _run_autorun_job() -> None:
    """Scheduler entry point (looked up at call time, so tests can stub it)."""
    maybe_run_autorun()


def start_scheduler(check_on_startup: bool = False) -> BackgroundScheduler | None:
    """Start the daily check (00:05 in ``TIMEZONE``). Returns None when disabled.

    00:05 is just after midnight, so on day ``AUTORUN_DAY + 1`` the run sees
    the registration window already closed. A run missed by up to
    ``MISFIRE_GRACE_SECONDS`` (host asleep) still fires once on wake-up.
    ``check_on_startup`` (the app lifespan) also runs the check right away in
    the scheduler thread, covering a host that was off for longer; the API
    does not wait for the solver.
    """
    if not settings.AUTORUN_ENABLED:
        return None
    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
    scheduler.add_job(
        _run_autorun_job,
        "cron",
        hour=0,
        minute=5,
        id="autorun",
        misfire_grace_time=MISFIRE_GRACE_SECONDS,
        coalesce=True,
    )
    if check_on_startup:
        scheduler.add_job(
            _run_autorun_job,
            "date",
            run_date=datetime.now(ZoneInfo(settings.TIMEZONE)),
            id="autorun-startup",
            misfire_grace_time=MISFIRE_GRACE_SECONDS,
        )
    scheduler.start()
    logger.info(
        "Autorun scheduler started (window closes after day %d; draft at 00:05 from "
        "day %d while next month has no schedule%s).",
        settings.AUTORUN_DAY, settings.AUTORUN_DAY + 1,
        "; checking now" if check_on_startup else "",
    )
    return scheduler
