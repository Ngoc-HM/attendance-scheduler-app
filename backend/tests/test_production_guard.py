"""Production hardening: env guard + seed-admin reset policy (blocker #1, review E)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import bootstrap
from app.core.config import Settings, settings
from app.core.database import SessionLocal
from app.models.user import User

STRONG_SECRET = "x" * 48
STRONG_PASSWORD = "correct-horse-battery"
DEFAULT_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/attendance"
# Everything a production process needs to pass the guard.
STRONG_PROD = {
    "SECRET_KEY": STRONG_SECRET,
    "FIRST_ADMIN_PASSWORD": STRONG_PASSWORD,
    "DATABASE_URL": "postgresql+psycopg2://attendance:db-pw@db.internal:5432/attendance",
    "BACKEND_CORS_ORIGINS": "https://scheduler.example.eu",
    "AUTO_CREATE_TABLES": False,
}


def _settings(**overrides) -> Settings:
    # _env_file=None: ignore backend/.env so the test is hermetic.
    return Settings(_env_file=None, **overrides)


def test_dev_never_blocks_startup() -> None:
    s = _settings(ENVIRONMENT="dev")
    assert s.production_config_errors() == []
    s.validate_for_environment()  # no raise


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_production_rejects_default_secret_and_password(env: str) -> None:
    s = _settings(
        ENVIRONMENT=env,
        SECRET_KEY="CHANGE_ME_dev_only_secret",
        FIRST_ADMIN_PASSWORD="admin123",
    )
    errors = s.production_config_errors()
    assert any("SECRET_KEY" in e for e in errors)
    assert any("FIRST_ADMIN_PASSWORD" in e for e in errors)
    with pytest.raises(RuntimeError, match="Refusing to start"):
        s.validate_for_environment()


def test_production_rejects_short_secret() -> None:
    s = _settings(ENVIRONMENT="prod", SECRET_KEY="short", FIRST_ADMIN_PASSWORD=STRONG_PASSWORD)
    assert any("SECRET_KEY" in e for e in s.production_config_errors())


def test_production_accepts_strong_settings_and_warns_on_risky_ones() -> None:
    s = _settings(ENVIRONMENT="prod", **STRONG_PROD, FIRST_ADMIN_RESET_ON_STARTUP=True)
    assert s.production_config_errors() == []
    s.validate_for_environment()
    warnings = s.production_config_warnings()
    assert any("FIRST_ADMIN_RESET_ON_STARTUP" in w for w in warnings)


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_prod_guard_refuses_sqlite_cors_star_autocreate_short_retention(env: str) -> None:
    """Review E: SQLite, the default Postgres URL, CORS '*', AUTO_CREATE_TABLES
    and a retention below the legal minimum are refused, not just logged."""
    s = _settings(
        ENVIRONMENT=env,
        SECRET_KEY=STRONG_SECRET,
        FIRST_ADMIN_PASSWORD=STRONG_PASSWORD,
        DATABASE_URL="sqlite:///./guard.db",
        BACKEND_CORS_ORIGINS="*",
        AUTO_CREATE_TABLES=True,
        DATA_RETENTION_MONTHS=12,
    )
    errors = s.production_config_errors()
    assert any("DATABASE_URL" in e and "SQLite" in e for e in errors)
    assert any("BACKEND_CORS_ORIGINS" in e for e in errors)
    assert any("AUTO_CREATE_TABLES" in e for e in errors)
    assert any("DATA_RETENTION_MONTHS" in e for e in errors)
    with pytest.raises(RuntimeError, match="Refusing to start"):
        s.validate_for_environment()

    # The shipped default URL (postgres:postgres@localhost) is refused too.
    default_url = _settings(
        ENVIRONMENT=env, **{**STRONG_PROD, "DATABASE_URL": DEFAULT_DATABASE_URL}
    )
    assert any("DATABASE_URL" in e for e in default_url.production_config_errors())

    # Retention exactly at the legal minimum is fine.
    at_minimum = _settings(ENVIRONMENT=env, **STRONG_PROD, DATA_RETENTION_MONTHS=24)
    assert at_minimum.production_config_errors() == []


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_prod_guard_retention_floor_cannot_be_lowered_by_env(env: str) -> None:
    """The legal 24-month floor is a constant: lowering DATA_RETENTION_MIN_MONTHS
    does not make a shorter retention acceptable; raising it does tighten it."""
    from app.core.config import LEGAL_RETENTION_FLOOR_MONTHS

    assert LEGAL_RETENTION_FLOOR_MONTHS == 24
    lowered = _settings(
        ENVIRONMENT=env, **STRONG_PROD, DATA_RETENTION_MIN_MONTHS=6, DATA_RETENTION_MONTHS=12
    )
    assert lowered.retention_floor_months == 24
    errors = lowered.production_config_errors()
    assert any("DATA_RETENTION_MIN_MONTHS" in e for e in errors)
    assert any("DATA_RETENTION_MONTHS=12" in e for e in errors)
    with pytest.raises(RuntimeError, match="Refusing to start"):
        lowered.validate_for_environment()

    # Lowering the floor alone is refused even when the retention is long.
    assert _settings(
        ENVIRONMENT=env, **STRONG_PROD, DATA_RETENTION_MIN_MONTHS=12
    ).production_config_errors()

    raised = _settings(
        ENVIRONMENT=env, **STRONG_PROD, DATA_RETENTION_MIN_MONTHS=48, DATA_RETENTION_MONTHS=36
    )
    assert raised.retention_floor_months == 48
    assert any("DATA_RETENTION_MONTHS=36" in e for e in raised.production_config_errors())


def test_dev_still_starts_with_sqlite_cors_star_and_autocreate() -> None:
    """The dev .env (SQLite or local PG, CORS '*', AUTO_CREATE_TABLES) runs."""
    s = _settings(
        ENVIRONMENT="dev",
        DATABASE_URL="sqlite:///./dev.db",
        BACKEND_CORS_ORIGINS="*",
        AUTO_CREATE_TABLES=True,
    )
    assert s.production_config_errors() == []
    s.validate_for_environment()


@pytest.mark.parametrize("env", ["dev", "prod"])
def test_invalid_timezone_refused_at_startup(env: str) -> None:
    """A typo in TIMEZONE must stop the process at settings load, in every
    environment — not crash the first leave request or the autorun."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="TIMEZONE"):
        _settings(ENVIRONMENT=env, TIMEZONE="Europe/Frankfurt")
    assert _settings(ENVIRONMENT=env, TIMEZONE="Europe/Berlin").TIMEZONE == "Europe/Berlin"


def test_api_docs_disabled_in_production(client: TestClient) -> None:
    from app.main import api_docs_urls

    for env in ("staging", "prod"):
        assert api_docs_urls(_settings(ENVIRONMENT=env, **STRONG_PROD)) == {
            "docs_url": None,
            "redoc_url": None,
            "openapi_url": None,
        }
    dev = api_docs_urls(_settings(ENVIRONMENT="dev"))
    assert dev["docs_url"] == "/docs"
    assert dev["openapi_url"] == "/api/v1/openapi.json"
    # The test process runs in dev: docs stay available.
    assert client.get("/api/v1/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_seed_admin_password_not_reset_outside_dev(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An admin who changed their password keeps it after a prod restart."""
    admin_tok = client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_tok}"}
    me = client.get("/api/v1/users/me", headers=headers).json()
    assert client.patch(
        f"/api/v1/users/{me['id']}", headers=headers, json={"password": "new-secret-99"}
    ).status_code == 200

    db = SessionLocal()
    try:
        before = db.query(User).filter(User.username == "admin").one().hashed_password
        monkeypatch.setattr(settings, "ENVIRONMENT", "prod")
        bootstrap.ensure_first_admin(db)
        after = db.query(User).filter(User.username == "admin").one().hashed_password
        assert after == before  # untouched in prod

        monkeypatch.setattr(settings, "ENVIRONMENT", "dev")
        bootstrap.ensure_first_admin(db)
        reset = db.query(User).filter(User.username == "admin").one().hashed_password
        assert reset != before  # dev convenience restores the default
    finally:
        db.close()

    # Back to the default so later tests can log in.
    assert client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
    ).status_code == 200


def test_autorun_day_leaves_room_for_the_next_day() -> None:
    """The draft runs on AUTORUN_DAY + 1, which must exist in every month."""
    from pydantic import ValidationError

    assert _settings(AUTORUN_DAY=1).AUTORUN_DAY == 1
    assert _settings(AUTORUN_DAY=27).AUTORUN_DAY == 27
    for bad in (0, 28, 31):
        with pytest.raises(ValidationError):
            _settings(AUTORUN_DAY=bad)
