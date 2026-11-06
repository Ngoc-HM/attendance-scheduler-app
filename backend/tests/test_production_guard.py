"""Production hardening: env guard + seed-admin reset policy (blocker #1)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import bootstrap
from app.core.config import Settings, settings
from app.core.database import SessionLocal
from app.models.user import User

STRONG_SECRET = "x" * 48
STRONG_PASSWORD = "correct-horse-battery"


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
    s = _settings(
        ENVIRONMENT="prod",
        SECRET_KEY=STRONG_SECRET,
        FIRST_ADMIN_PASSWORD=STRONG_PASSWORD,
        AUTO_CREATE_TABLES=True,
        BACKEND_CORS_ORIGINS="*",
    )
    assert s.production_config_errors() == []
    s.validate_for_environment()
    warnings = s.production_config_warnings()
    assert any("AUTO_CREATE_TABLES" in w for w in warnings)
    assert any("CORS" in w for w in warnings)


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
