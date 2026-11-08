"""Startup bootstrap (review B7/B8/E): seed admin, create_all, database creation.

Each test that needs a pristine database builds its own throwaway SQLite file,
so the shared test database (and its seed admin) is never touched.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core import bootstrap
from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.enums import Role, UserStatus
from app.models.user import User
from app.services.user_service import next_user_code


@pytest.fixture
def fresh_engine(tmp_path: Path) -> Iterator[Engine]:
    engine = create_engine(f"sqlite:///{tmp_path / 'boot.db'}")
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def fresh_db(fresh_engine: Engine) -> Iterator[Session]:
    Base.metadata.create_all(bind=fresh_engine)
    db = sessionmaker(bind=fresh_engine, autoflush=False)()
    try:
        yield db
    finally:
        db.close()


def _usernames(db: Session) -> set[str]:
    return {u for (u,) in db.query(User.username).all()}


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_deleted_seed_admin_not_recreated_when_another_active_admin_exists(
    fresh_db: Session, monkeypatch: pytest.MonkeyPatch, env: str
) -> None:
    """B7: the seed admin is a first-run bootstrap only. Once another active
    admin exists and the seed account was deleted, a restart must not bring
    it back (with the default password) — in dev or prod."""
    monkeypatch.setattr(settings, "ENVIRONMENT", env)
    monkeypatch.setattr(settings, "FIRST_ADMIN_USERNAME", "seed-admin")

    # Empty database: the seed admin is created.
    bootstrap.ensure_first_admin(fresh_db)
    assert _usernames(fresh_db) == {"seed-admin"}

    # A real admin takes over and deletes the seed account.
    fresh_db.add(
        User(
            username="real-admin",
            code=next_user_code(fresh_db, Role.M),
            full_name="Real Admin",
            hashed_password=get_password_hash("real-admin-pw"),
            role=Role.M,
            status=UserStatus.active,
        )
    )
    fresh_db.query(User).filter(User.username == "seed-admin").delete()
    fresh_db.commit()

    bootstrap.ensure_first_admin(fresh_db)
    assert _usernames(fresh_db) == {"real-admin"}

    # Locked out (no ACTIVE admin left): the seed admin comes back.
    fresh_db.query(User).filter(User.username == "real-admin").update(
        {User.status: UserStatus.disabled}
    )
    fresh_db.commit()
    bootstrap.ensure_first_admin(fresh_db)
    assert _usernames(fresh_db) == {"real-admin", "seed-admin"}


def test_create_all_skipped_when_alembic_version_table_exists(
    fresh_engine: Engine, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """B8: once Alembic manages the database, AUTO_CREATE_TABLES must not
    create tables behind its back (the next 'alembic upgrade' would then hit
    DuplicateTable)."""
    monkeypatch.setattr(bootstrap, "engine", fresh_engine)
    monkeypatch.setattr(settings, "AUTO_CREATE_TABLES", True)
    with fresh_engine.begin() as conn:
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))

    with caplog.at_level(logging.WARNING, logger="app.core.bootstrap"):
        bootstrap.create_tables_if_enabled()

    assert inspect(fresh_engine).get_table_names() == ["alembic_version"]
    assert any(
        r.levelno == logging.WARNING and "alembic_version" in r.getMessage()
        for r in caplog.records
    )


def test_create_all_runs_on_a_database_without_alembic(
    fresh_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bootstrap, "engine", fresh_engine)
    monkeypatch.setattr(settings, "AUTO_CREATE_TABLES", True)

    bootstrap.create_tables_if_enabled()

    assert "users" in inspect(fresh_engine).get_table_names()


@pytest.mark.parametrize(("env", "expected"), [("dev", True), ("prod", False)])
def test_ensure_database_exists_only_outside_production(
    monkeypatch: pytest.MonkeyPatch, env: str, expected: bool
) -> None:
    """A production process must not try CREATE DATABASE on the server."""
    calls: list[str] = []
    monkeypatch.setattr(settings, "ENVIRONMENT", env)
    monkeypatch.setattr(bootstrap, "ensure_database_exists", lambda: calls.append("x"))
    monkeypatch.setattr(bootstrap, "create_tables_if_enabled", lambda: None)
    monkeypatch.setattr(bootstrap, "ensure_first_admin", lambda db: None)
    monkeypatch.setattr(bootstrap, "ensure_default_flight_presets", lambda db: None)

    bootstrap.run_startup_bootstrap()

    assert bool(calls) is expected


def test_app_logger_prints_info() -> None:
    """C4: the app.* loggers emit INFO through their own handler, so autorun
    and bootstrap messages reach the uvicorn console."""
    import app.main  # noqa: F401  (configures logging on import)

    app_logger = logging.getLogger("app")
    assert app_logger.getEffectiveLevel() == logging.INFO
    assert logging.getLogger("app.services.schedule_autorun").isEnabledFor(logging.INFO)
    assert any(isinstance(h, logging.StreamHandler) for h in app_logger.handlers)
