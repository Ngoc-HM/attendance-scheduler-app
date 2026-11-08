"""Alembic migration environment.

The database URL and target metadata are pulled from the application so there
is a single source of truth. ``import app.models`` ensures every model is
registered on ``Base.metadata`` for autogenerate.

SQLite: ``app.core.database`` turns foreign keys ON for every SQLite
connection, but batch migrations (0003, 0008) rebuild a table by copy + DROP +
rename, and SQLite refuses to drop a referenced table while foreign keys are
enforced. They are therefore switched OFF for the migration run and back ON
afterwards.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.models  # noqa: F401  (register all models on Base.metadata)
from app.core.config import settings
from app.core.database import Base

config = context.config
# Alembic's config is a ConfigParser: a bare '%' (a URL-encoded password, say)
# would start an interpolation and abort the run, so it is doubled here.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        if is_sqlite:
            # PRAGMA foreign_keys is ignored inside a transaction: set it
            # before the migration transaction begins.
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
        try:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if is_sqlite:
                connection.rollback()  # ends a failed transaction, else a no-op
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
