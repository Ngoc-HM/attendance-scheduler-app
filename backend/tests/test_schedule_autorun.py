"""Autorun catch-up and diagnostics (review C4).

The months used here (2036-2037) are touched by no other test file.
"""

from __future__ import annotations

import logging
import time
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.flight import FlightDay
from app.models.schedule import MonthlySchedule
from app.services import schedule_autorun
from app.services.schedule_autorun import maybe_run_autorun, start_scheduler

LOGGER = "app.services.schedule_autorun"


@pytest.fixture
def autorun_on(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable autorun only after the ``client`` lifespan has started, so the
    app's startup check never runs with it on (it would use the real date)."""
    monkeypatch.setattr(settings, "AUTORUN_ENABLED", True)
    monkeypatch.setattr(settings, "AUTORUN_DAY", 20)
    monkeypatch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", 5.0)


def _schedule_exists(year: int, month: int) -> bool:
    db = SessionLocal()
    try:
        return (
            db.query(MonthlySchedule)
            .filter(MonthlySchedule.year == year, MonthlySchedule.month == month)
            .one_or_none()
            is not None
        )
    finally:
        db.close()


def test_autorun_catches_up_after_missed_day(client: TestClient, autorun_on: None) -> None:
    """The machine was off at 00:05 on day 21: on day 23 the next month still
    has no schedule, so the run generates it instead of losing the month."""
    assert maybe_run_autorun(date(2036, 3, 20)) is False  # window still open
    assert not _schedule_exists(2036, 4)

    assert maybe_run_autorun(date(2036, 3, 23)) is True
    assert _schedule_exists(2036, 4)
    # Already there: later days and restarts never regenerate it.
    assert maybe_run_autorun(date(2036, 3, 28)) is False


def test_autorun_does_nothing_before_the_window_closes(
    client: TestClient, autorun_on: None
) -> None:
    for day in (1, 15, 20):
        assert maybe_run_autorun(date(2036, 5, day)) is False
    assert not _schedule_exists(2036, 6)


def test_autorun_logs_failure_when_infeasible(
    client: TestClient,
    autorun_on: None,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An infeasible solve saves nothing; it must be an ERROR, not a cheerful
    'generated draft' line, and must not count as a run."""
    from app.services import schedule_service
    from app.services.schedule_service import ScheduleResult

    monkeypatch.setattr(
        schedule_service,
        "generate",
        lambda db, year, month: ScheduleResult(feasible=False, violations=[]),
    )
    with caplog.at_level(logging.INFO, logger=LOGGER):
        assert maybe_run_autorun(date(2036, 7, 21)) is False

    errors = [r for r in caplog.records if r.name == LOGGER and r.levelno == logging.ERROR]
    assert errors and "2036-08" in errors[0].getMessage()
    assert not any("generated draft" in r.getMessage() for r in caplog.records)
    assert not _schedule_exists(2036, 8)


def test_autorun_logs_exception_as_error(
    client: TestClient,
    autorun_on: None,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from app.services import schedule_service

    def boom(db, year, month):  # noqa: ANN001, ANN202
        raise RuntimeError("solver exploded")

    monkeypatch.setattr(schedule_service, "generate", boom)
    with caplog.at_level(logging.INFO, logger=LOGGER):
        assert maybe_run_autorun(date(2036, 9, 22)) is False
    assert any(
        r.name == LOGGER and r.levelno == logging.ERROR and "2036-10" in r.getMessage()
        for r in caplog.records
    )


def test_autorun_warns_without_flight_data(
    client: TestClient, autorun_on: None, caplog: pytest.LogCaptureFixture
) -> None:
    """No FlightDay rows for the next month means the draft is planned without
    flights — still generated, but loudly flagged so the admin enters them."""
    with caplog.at_level(logging.INFO, logger=LOGGER):
        assert maybe_run_autorun(date(2036, 11, 21)) is True
    warnings = [
        r for r in caplog.records if r.name == LOGGER and r.levelno == logging.WARNING
    ]
    assert warnings and "2036-12" in warnings[0].getMessage()
    assert "flight" in warnings[0].getMessage().lower()


def test_autorun_quiet_when_flight_data_present(
    client: TestClient, autorun_on: None, caplog: pytest.LogCaptureFixture
) -> None:
    db = SessionLocal()
    try:
        db.add(FlightDay(day=date(2037, 2, 3), flight_pairs=1))
        db.commit()
    finally:
        db.close()
    try:
        with caplog.at_level(logging.INFO, logger=LOGGER):
            assert maybe_run_autorun(date(2037, 1, 21)) is True
        assert not any(
            r.name == LOGGER and r.levelno == logging.WARNING for r in caplog.records
        )
    finally:
        db = SessionLocal()
        try:
            db.query(FlightDay).filter(FlightDay.day == date(2037, 2, 3)).delete()
            db.commit()
        finally:
            db.close()


def test_scheduler_tolerates_late_wakeup_and_checks_at_startup(
    autorun_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The daily job still fires when the host wakes up within an hour of
    00:05, and a startup check covers longer outages."""
    calls: list[str] = []
    monkeypatch.setattr(schedule_autorun, "maybe_run_autorun", lambda: calls.append("run"))

    scheduler = start_scheduler(check_on_startup=False)
    assert scheduler is not None
    try:
        daily = scheduler.get_job("autorun")
        assert daily.misfire_grace_time == 3600
        assert daily.coalesce is True
        assert scheduler.get_job("autorun-startup") is None
    finally:
        scheduler.shutdown(wait=False)

    # The startup check runs in the scheduler thread (the solver may take a
    # while; the API must not wait for it).
    scheduler = start_scheduler(check_on_startup=True)
    assert scheduler is not None
    try:
        deadline = time.monotonic() + 10
        while not calls and time.monotonic() < deadline:
            time.sleep(0.05)
    finally:
        scheduler.shutdown(wait=True)
    assert calls == ["run"]
