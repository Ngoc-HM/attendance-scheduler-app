"""A DATABASE_URL without a driver must use the project's driver (psycopg2).

SQLAlchemy 2.1 reads a bare ``postgresql://`` as psycopg 3, which is not in
requirements.txt, so such a URL failed at import with "No module named
'psycopg'" (found on the owner's .env, 2026-11-10).
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from app.core.config import Settings

WITH_DRIVER = "postgresql+psycopg2://user:p%40ss@db.internal:5432/attendance?sslmode=require"


def _settings(**overrides) -> Settings:
    # _env_file=None: ignore backend/.env so the test is hermetic.
    return Settings(_env_file=None, **overrides)


@pytest.mark.parametrize(
    "given",
    [
        "postgresql://user:p%40ss@db.internal:5432/attendance?sslmode=require",
        "postgres://user:p%40ss@db.internal:5432/attendance?sslmode=require",
    ],
)
def test_driverless_postgres_url_uses_psycopg2(given: str) -> None:
    url = _settings(DATABASE_URL=given).DATABASE_URL
    assert url == WITH_DRIVER
    # create_engine imports the driver the URL names; it does not connect.
    assert create_engine(url).driver == "psycopg2"


def test_driverless_url_from_the_environment_is_normalised(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@db.internal/attendance")
    assert _settings().DATABASE_URL == "postgresql+psycopg2://user:pw@db.internal/attendance"


@pytest.mark.parametrize(
    "given",
    [
        WITH_DRIVER,
        "postgresql+psycopg://user:pw@db.internal/attendance",
        "sqlite:///./local.db",
    ],
)
def test_url_with_a_driver_or_sqlite_is_untouched(given: str) -> None:
    assert _settings(DATABASE_URL=given).DATABASE_URL == given
