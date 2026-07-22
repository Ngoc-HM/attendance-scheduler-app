"""add role F to the role enum (split from T, owner 2026-07-09)

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-09
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres role is a native ENUM; SQLite (tests) stores plain text — no-op.
    if op.get_bind().dialect.name == "postgresql":
        # ADD VALUE cannot run inside the implicit transaction on PG < 12;
        # on supported versions IF NOT EXISTS makes this idempotent.
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'F'")


def downgrade() -> None:
    # Removing an enum value in Postgres is unsafe (requires type rebuild and
    # would break rows already using 'F'). Leave the value in place.
    pass
