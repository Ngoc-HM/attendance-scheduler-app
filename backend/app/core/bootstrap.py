"""Startup bootstrap: schema (dev) and the first admin account (F-01).

Called from the FastAPI lifespan on startup. Two jobs:

1. (dev) create tables so the API runs locally without an Alembic step;
   production should manage schema with migrations instead. Skipped once the
   database carries ``alembic_version`` (Alembic owns the schema then).
2. Ensure an admin can log in: the seed admin (role M) is created only while
   no ACTIVE admin exists, so a seed account an admin deleted on purpose is
   not resurrected on the next restart. In DEV only
   (``FIRST_ADMIN_RESET_ON_STARTUP``), an existing seed admin has its
   password reset to the configured default so local login is one click.
   In staging/prod an existing admin's credentials are never touched.
"""

from __future__ import annotations

import logging
from datetime import time

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.enums import Role, UserStatus
from app.models.flight import FlightPreset
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
    if not settings.AUTO_CREATE_TABLES:
        return
    if inspect(engine).has_table("alembic_version"):
        # create_all would add tables a later migration also creates, and
        # 'alembic upgrade' would then fail with DuplicateTable.
        logger.warning(
            "AUTO_CREATE_TABLES ignored: the database has an alembic_version table, "
            "so its schema is managed by Alembic ('alembic upgrade head')."
        )
        return
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured (AUTO_CREATE_TABLES=on).")


def ensure_first_admin(db: Session) -> User | None:
    """Create the seed admin; reset its password only in dev (see module doc).

    Returns the seed admin, or None when it is absent and another active
    admin exists (it was deleted on purpose and stays deleted).
    """
    admin = (
        db.query(User)
        .filter(User.username == settings.FIRST_ADMIN_USERNAME)
        .one_or_none()
    )

    if admin is None:
        other_admin = (
            db.query(User.username)
            .filter(User.role == Role.M, User.status == UserStatus.active)
            .first()
        )
        if other_admin is not None:
            logger.info(
                "Seed admin '%s' not created: active admin '%s' exists.",
                settings.FIRST_ADMIN_USERNAME, other_admin[0],
            )
            return None
        admin = User(
            username=settings.FIRST_ADMIN_USERNAME,
            full_name=settings.FIRST_ADMIN_FULL_NAME,
            hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
            role=Role.M,
            status=UserStatus.active,
            code=next_user_code(db, Role.M),
        )
        db.add(admin)
        logger.info("Seed admin '%s' created.", settings.FIRST_ADMIN_USERNAME)
    elif settings.FIRST_ADMIN_RESET_ON_STARTUP and not settings.is_production:
        # DEV convenience only: restore the default password / role / status.
        admin.hashed_password = get_password_hash(settings.FIRST_ADMIN_PASSWORD)
        admin.role = Role.M
        admin.status = UserStatus.active
        if admin.code is None:
            admin.code = next_user_code(db, Role.M)
        logger.info(
            "Seed admin '%s' password reset to the dev default (ENVIRONMENT=dev).",
            settings.FIRST_ADMIN_USERNAME,
        )
    else:
        # Production-like: never touch an existing admin's credentials, role
        # or status. Only backfill a missing code (pre-migration databases).
        if admin.code is None:
            admin.code = next_user_code(db, Role.M)
        logger.info(
            "Seed admin '%s' present; credentials left unchanged (ENVIRONMENT=%s).",
            settings.FIRST_ADMIN_USERNAME, settings.ENVIRONMENT,
        )

    db.commit()
    db.refresh(admin)
    return admin


def ensure_default_flight_presets(db: Session) -> None:
    """Insert the two standard presets if the flight_presets table is empty.

    Idempotent: only seeds when the table is empty so admin edits are never
    overwritten on restart.
    """
    if db.query(FlightPreset).count() > 0:
        return

    defaults = [
        FlightPreset(
            label="HAN–FRA (37/36)",
            route="HAN-FRA",
            flt_arr=37,
            flt_dep=36,
            sta=time(6, 0),
            std=time(13, 55),
            sort_order=0,
        ),
        FlightPreset(
            label="SGN–FRA (31/30)",
            route="SGN-FRA",
            flt_arr=31,
            flt_dep=30,
            sta=time(6, 30),
            std=time(13, 35),
            sort_order=1,
        ),
    ]
    for preset in defaults:
        db.add(preset)
    db.commit()
    logger.info("Default flight presets seeded (%d rows).", len(defaults))


def run_startup_bootstrap() -> None:
    """Entry point for the app lifespan."""
    # Dev convenience only: a production process never issues CREATE DATABASE
    # (its role should not be allowed to, and a typo must fail loudly).
    if not settings.is_production:
        ensure_database_exists()
    create_tables_if_enabled()
    db = SessionLocal()
    try:
        ensure_first_admin(db)
        ensure_default_flight_presets(db)
    finally:
        db.close()
