"""Maintenance-script guard (#33): run only against a LOCAL database in dev.

The owner's own ``.env`` says ENVIRONMENT=dev but points at a remote Postgres,
so "dev" alone does not prove the database is a throwaway one.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.script_guard import is_local_database, refuse_unless_safe

REMOTE = "postgresql+psycopg2://owner:s3cret-pw@db.example-cloud.eu:5432/attendance"


@pytest.mark.parametrize(
    "url",
    [
        "sqlite:///./attendance.db",
        "sqlite://",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/attendance",
        "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/attendance",
        "postgresql+psycopg2://postgres:postgres@[::1]:5432/attendance",
    ],
)
def test_sqlite_and_loopback_hosts_are_local(url: str) -> None:
    assert is_local_database(url) is True


@pytest.mark.parametrize(
    "url",
    [
        REMOTE,
        "postgresql+psycopg2://postgres:postgres@10.0.0.5:5432/attendance",
        # No host: libpq may still pick one from PGHOST — not provably local.
        "postgresql+psycopg2:///attendance",
    ],
)
def test_other_hosts_are_not_local(url: str) -> None:
    assert is_local_database(url) is False


def _settings(environment: str, url: str) -> SimpleNamespace:
    return SimpleNamespace(ENVIRONMENT=environment, DATABASE_URL=url)


def test_dev_with_local_database_passes() -> None:
    assert refuse_unless_safe(_settings("dev", "sqlite:///./attendance.db"), allow=False) is None


def test_dev_with_remote_database_refuses(capsys: pytest.CaptureFixture[str]) -> None:
    assert refuse_unless_safe(_settings("dev", REMOTE), allow=False) == 2

    err = capsys.readouterr().err
    assert "db.example-cloud.eu" in err
    assert "s3cret-pw" not in err
    assert "--allow-non-dev" in err


@pytest.mark.parametrize("environment", ["staging", "prod"])
def test_non_dev_with_local_database_refuses(environment: str) -> None:
    url = "postgresql+psycopg2://postgres:postgres@localhost:5432/attendance"
    assert refuse_unless_safe(_settings(environment, url), allow=False) == 2


@pytest.mark.parametrize(("environment", "url"), [("dev", REMOTE), ("prod", REMOTE)])
def test_allow_non_dev_passes(environment: str, url: str) -> None:
    assert refuse_unless_safe(_settings(environment, url), allow=True) is None
