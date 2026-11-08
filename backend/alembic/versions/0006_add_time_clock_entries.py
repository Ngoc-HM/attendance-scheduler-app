"""add time_clock_entries table (check-in/out, owner 2026-07-09)

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "time_clock_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "work_date", name="uq_time_clock_cell"),
    )
    op.create_index(
        "ix_time_clock_entries_user_id", "time_clock_entries", ["user_id"]
    )
    op.create_index(
        "ix_time_clock_entries_work_date", "time_clock_entries", ["work_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_time_clock_entries_work_date", table_name="time_clock_entries")
    op.drop_index("ix_time_clock_entries_user_id", table_name="time_clock_entries")
    op.drop_table("time_clock_entries")
