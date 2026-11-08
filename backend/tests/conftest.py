"""Shared pytest fixtures.

The test suite runs against an isolated SQLite database so it needs neither a
running PostgreSQL nor the psycopg2 driver. The DB environment is configured
*before* importing the app, because the engine is built from settings at
import time.

A ``DATABASE_URL`` that is already set (CI's localhost PostgreSQL) is kept,
but only when it is local: the suite deletes and rewrites rows, so a URL that
points at a shared server stops the run before anything connects.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from app.core.script_guard import is_local_database

# --- Refuse a non-local database before anything can connect to it. --------
_PRESET_URL = os.environ.get("DATABASE_URL")
if _PRESET_URL and not is_local_database(_PRESET_URL):
    pytest.exit("refusing to run tests against a non-local database")

# --- Configure an isolated SQLite DB before the app/engine is imported. ----
_TEST_DB = os.path.join(tempfile.mkdtemp(prefix="asa_test_"), "test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB}")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("FIRST_ADMIN_USERNAME", "admin")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "admin123")
os.environ.setdefault("SECRET_KEY", "test-secret")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Client whose context manager runs the lifespan (tables + seed admin)."""
    with TestClient(app) as c:
        yield c
