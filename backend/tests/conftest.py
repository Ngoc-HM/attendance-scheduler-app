"""Shared pytest fixtures.

The test suite runs against an isolated SQLite database so it needs neither a
running PostgreSQL nor the psycopg2 driver. The DB environment is configured
*before* importing the app, because the engine is built from settings at
import time.
"""

from __future__ import annotations

import os
import tempfile

# --- Configure an isolated SQLite DB before the app/engine is imported. ----
_TEST_DB = os.path.join(tempfile.mkdtemp(prefix="asa_test_"), "test.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB}")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("FIRST_ADMIN_USERNAME", "admin")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "admin123")
os.environ.setdefault("SECRET_KEY", "test-secret")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Client whose context manager runs the lifespan (tables + seed admin)."""
    with TestClient(app) as c:
        yield c
