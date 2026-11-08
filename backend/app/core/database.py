"""Database engine, session factory and the declarative ``Base``.

A single PostgreSQL database is shared by all clients (spec §2). Schema
changes are managed by Alembic migrations (see ``alembic/``), not by
``create_all`` in production.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
    """Enforce foreign keys on every SQLite connection, app and tests alike.

    SQLite ignores ``FOREIGN KEY`` clauses unless this pragma is set per
    connection, so a delete that PostgreSQL rejects would silently pass in the
    test suite. Registered on the ``Engine`` class, it covers every engine.
    """
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
