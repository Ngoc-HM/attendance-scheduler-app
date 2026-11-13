"""mark a time-clock day the admin set by hand

``corrected_by`` is the admin who last set the day's punches
(``PUT /attendance/clock/staff``); NULL means the person punched it
themself. The admin board shows such a day as corrected by hand.

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("time_clock_entries") as batch:
        batch.add_column(sa.Column("corrected_by", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_time_clock_corrected_by",
            "users",
            ["corrected_by"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("time_clock_entries") as batch:
        batch.drop_constraint("fk_time_clock_corrected_by", type_="foreignkey")
        batch.drop_column("corrected_by")
