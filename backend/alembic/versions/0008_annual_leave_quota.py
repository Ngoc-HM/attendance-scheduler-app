"""annual leave quota replaces the unused annual_leave_balance (owner decision D4)

Each user gets an admin-set ``annual_leave_quota`` (days per calendar year);
the remaining balance is derived from approved leave, so the never-used
``annual_leave_balance`` column is dropped. Existing users start at 30 days —
the same placeholder as ``ANNUAL_LEAVE_DEFAULT_DAYS`` until the customer
confirms the real figure.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-06
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "annual_leave_quota", sa.Integer(), nullable=False, server_default="30"
        ),
    )
    # Batch mode so SQLite (which cannot DROP COLUMN in older versions) works.
    with op.batch_alter_table("users") as batch:
        batch.drop_column("annual_leave_balance")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "annual_leave_balance",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.drop_column("annual_leave_quota")
