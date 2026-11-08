"""Maintenance-script guard (#33): run only against a LOCAL database in dev.

The owner's own ``.env`` says ENVIRONMENT=dev but points at a remote Postgres,
so "dev" alone does not prove the database is a throwaway one.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.script_guard import is_local_database, refuse_unless_safe

REMOTE = "postgresql+psycopg2://owner:s3cret-pw@db.example-cloud.eu:5432/attendance"
BACKEND_ROOT = Path(__file__).resolve().parents[1]


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


@pytest.mark.parametrize(
    "url",
    [
        # libpq takes host/hostaddr/service from the query string over the
        # netloc: "localhost" in the URL proves nothing.
        "postgresql+psycopg2://u:p@localhost:5432/attendance?host=db.example-cloud.eu",
        "postgresql+psycopg2://u:p@127.0.0.1/attendance?hostaddr=10.0.0.5",
        "postgresql+psycopg2://u:p@localhost/attendance?service=prod",
        "postgresql+psycopg2://u:p@localhost/attendance?sslmode=require&HOST=db.remote",
    ],
)
def test_guard_rejects_query_host(url: str) -> None:
    assert is_local_database(url) is False
    assert refuse_unless_safe(_settings("dev", url), allow=False) == 2


def test_guard_keeps_harmless_query_params_local() -> None:
    url = "postgresql+psycopg2://u:p@localhost:5432/attendance?sslmode=disable"
    assert is_local_database(url) is True


def test_load_backend_env_reads_the_given_file_without_overriding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.script_guard import load_backend_env

    env_file = tmp_path / ".env"
    env_file.write_text(
        "ASA_PROBE_FROM_FILE=from-file\nASA_PROBE_PRESET=from-file\n", encoding="utf-8"
    )
    monkeypatch.delenv("ASA_PROBE_FROM_FILE", raising=False)
    monkeypatch.setenv("ASA_PROBE_PRESET", "from-shell")
    monkeypatch.chdir(tmp_path.parent)  # the cwd plays no part

    assert load_backend_env(env_file) is True
    assert os.environ["ASA_PROBE_FROM_FILE"] == "from-file"
    assert os.environ["ASA_PROBE_PRESET"] == "from-shell"  # the shell wins
    monkeypatch.delenv("ASA_PROBE_FROM_FILE")

    assert load_backend_env(tmp_path / "missing.env") is False


@pytest.mark.parametrize("script", ["reset_all_passwords.py", "seed_demo_users.py"])
def test_scripts_load_backend_env_by_absolute_path(
    script: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run from the repo root, the scripts used to miss backend/.env (the
    settings read '.env' relative to the cwd) and fell back to defaults. They
    must load backend/.env by its absolute path, before the settings import.
    The loader is stubbed: the real backend/.env is never read here."""
    from app.core import script_guard

    seen: list[Path] = []
    monkeypatch.setattr(script_guard, "load_backend_env", seen.append)
    monkeypatch.chdir(BACKEND_ROOT.parent)

    path = BACKEND_ROOT / "scripts" / script
    spec = importlib.util.spec_from_file_location(f"_script_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(importlib.util.module_from_spec(spec))

    assert seen == [BACKEND_ROOT / ".env"]
    assert seen[0].is_absolute()
    source = path.read_text(encoding="utf-8")
    assert source.index("load_backend_env(") < source.index("from app.core.config import")


def test_read_password_prompts_twice_when_not_given(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import script_guard

    prompts: list[str] = []
    answers = iter(["s3cret-local-pw", "s3cret-local-pw"])

    def fake_getpass(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(script_guard.getpass, "getpass", fake_getpass)
    assert script_guard.read_password(None) == "s3cret-local-pw"
    assert len(prompts) == 2

    # --password keeps working for non-interactive use (no prompt).
    assert script_guard.read_password("given-on-cli") == "given-on-cli"
    assert len(prompts) == 2


@pytest.mark.parametrize("answers", [["one-pw", "other-pw"], ["", ""]])
def test_read_password_refuses_mismatch_or_empty(
    answers: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from app.core import script_guard

    it = iter(answers)
    monkeypatch.setattr(script_guard.getpass, "getpass", lambda prompt="": next(it))
    assert script_guard.read_password(None) is None
    out = capsys.readouterr()
    assert out.err  # says why
    for answer in filter(None, answers):
        assert answer not in out.err + out.out  # never echoes a password


def test_read_password_refuses_empty_cli_value(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--password ""`` is refused like an empty prompt, without prompting."""
    from app.core import script_guard

    def no_prompt(prompt: str = "") -> str:
        raise AssertionError("must not prompt when --password is given")

    monkeypatch.setattr(script_guard.getpass, "getpass", no_prompt)
    assert script_guard.read_password("") is None
    assert "empty" in capsys.readouterr().err
