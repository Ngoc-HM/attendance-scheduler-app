"""store the working-time frame of shifts A and D

``shift_times`` holds one row per single shift (``A``, ``D``) with its start
and end; the admin edits them. The double shift's frame (A/D, AD) is derived
from the two rows, never stored. Seeded with the owner's defaults:
A 05:30-13:05, D 06:20-13:55.

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-18
"""

from __future__ import annotations

from datetime import time
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A new table needs no batch mode on SQLite (nothing is altered).
    table = op.create_table(
        "shift_times",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=4), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_shift_times_code"),
    )
    op.bulk_insert(
        table,
        [
            {"code": "A", "start_time": time(5, 30), "end_time": time(13, 5)},
            {"code": "D", "start_time": time(6, 20), "end_time": time(13, 55)},
        ],
    )


def downgrade() -> None:
    op.drop_table("shift_times")
