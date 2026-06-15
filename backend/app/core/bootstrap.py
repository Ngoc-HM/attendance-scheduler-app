"""Startup bootstrap: schema (dev) and the first admin account (F-01).

Called from the FastAPI lifespan on startup. Two jobs:

1. (dev) create tables so the API runs locally without an Alembic step;
   production should manage schema with migrations instead.
2. Ensure the seed admin (role M) exists. Per requirement: create it if
   missing, otherwise RESET its password back to the configured default.
   Users may change the password at runtime, but a restart restores it.
"""

from __future__ import annotations

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.enums import Role, UserStatus
from app.models.user import User
from app.services.user_service import next_user_code

logger = logging.getLogger(__name__)


def ensure_database_exists() -> None:
    """Create the target database if it does not exist yet.

    Postgres cannot create a database via ``create_all``; we connect to the
    maintenance ``postgres`` database and issue ``CREATE DATABASE`` when the
    target is missing. SQLite needs nothing (the file is created on connect).
    """
    url = make_url(settings.DATABASE_URL)
    if not url.get_backend_name().startswith("postgresql"):
        return  # SQLite / others create storage on demand.

    db_name = url.database
    if not db_name:
        return

    # CREATE DATABASE must run outside a transaction → AUTOCOMMIT.
    admin_engine = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"),
                {"n": db_name},
            ).scalar()
            if not exists:
                # db_name is an identifier (not a bound param) — quote it.
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info("Database %r created.", db_name)
            else:
                logger.info("Database %r already exists.", db_name)
    finally:
        admin_engine.dispose()


def create_tables_if_enabled() -> None:
    """Create all tables in dev (``AUTO_CREATE_TABLES``). No-op otherwise.

    FRESH-DB CONVENIENCE ONLY: ``create_all`` never ALTERs existing tables.
    Schema changes are managed with Alembic (``alembic upgrade head``);
    existing databases created this way are stamped at the baseline revision
    (see ``alembic/versions/0001_baseline.py``).
    """
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured (AUTO_CREATE_TABLES=on).")


def ensure_first_admin(db: Session) -> User:
    """Create the seed admin, or reset its password to the configured default."""
    hashed = get_password_hash(settings.FIRST_ADMIN_PASSWORD)
    admin = (
        db.query(User)
        .filter(User.username == settings.FIRST_ADMIN_USERNAME)
        .one_or_none()
    )

    if admin is None:
        admin = User(
            username=settings.FIRST_ADMIN_USERNAME,
            full_name=settings.FIRST_ADMIN_FULL_NAME,
            hashed_password=hashed,
            role=Role.M,
            status=UserStatus.active,
            code=next_user_code(db, Role.M),
        )
        db.add(admin)
        logger.info("Seed admin '%s' created.", settings.FIRST_ADMIN_USERNAME)
    else:
        # Reset to the default password and keep the account usable.
        admin.hashed_password = hashed
        admin.role = Role.M
        admin.status = UserStatus.active
        # Backfill code if it was never set (e.g. pre-migration existing admin).
        if admin.code is None:
            admin.code = next_user_code(db, Role.M)
        logger.info(
            "Seed admin '%s' password reset to default.",
            settings.FIRST_ADMIN_USERNAME,
        )

    db.commit()
    db.refresh(admin)
    return admin


def run_startup_bootstrap() -> None:
    """Entry point for the app lifespan."""
    ensure_database_exists()
    create_tables_if_enabled()
    db = SessionLocal()
    try:
        ensure_first_admin(db)
    finally:
        db.close()
