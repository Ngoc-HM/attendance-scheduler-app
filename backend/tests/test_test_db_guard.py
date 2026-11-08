"""The test suite refuses a non-local ``DATABASE_URL`` (review 2026-11-08 B9)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def _collect_with(url: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "DATABASE_URL": url}
    return subprocess.run(
        [
            sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
            "-o", "addopts=", "--collect-only", "-q", "tests/test_health.py",
        ],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_non_local_database_url_stops_the_run() -> None:
    result = _collect_with("postgresql+psycopg2://u:p@db.example.com:5432/prod")
    # pytest.exit raised while loading conftest ends the run as a usage error.
    assert result.returncode != 0
    assert "refusing to run tests against a non-local database" in (
        result.stdout + result.stderr
    )


def test_local_sqlite_url_is_allowed(tmp_path: Path) -> None:
    result = _collect_with(f"sqlite:///{tmp_path / 'guard.db'}")
    assert result.returncode == 0, result.stdout + result.stderr
