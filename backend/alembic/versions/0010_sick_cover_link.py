"""link an A/D sick cover to the sick day it covers

``cover_of_id`` points from the colleague's A/D actual to the sick (S) actual
it was assigned for; ``cover_prev_code`` / ``cover_prev_seeded`` keep what
that cell held before. When the admin takes the S back (recorded by mistake),
the cover is restored instead of leaving two people on the same shift.

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Stored labels are the enum member names (see 0001).
_CODES = ("A", "D", "A_D", "AD", "X", "CD", "O_D", "T", "B", "S", "AL")


def upgrade() -> None:
    with op.batch_alter_table("attendance_records") as batch:
        batch.add_column(sa.Column("cover_of_id", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column(
                "cover_prev_code",
                sa.Enum(*_CODES, name="attendance_code", create_type=False),
                nullable=True,
            )
        )
        batch.add_column(
            sa.Column(
                "cover_prev_seeded",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.create_foreign_key(
            "fk_attendance_cover_of",
            "attendance_records",
            ["cover_of_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_attendance_records_cover_of_id", ["cover_of_id"])


def downgrade() -> None:
    with op.batch_alter_table("attendance_records") as batch:
        batch.drop_index("ix_attendance_records_cover_of_id")
        batch.drop_constraint("fk_attendance_cover_of", type_="foreignkey")
        batch.drop_column("cover_prev_seeded")
        batch.drop_column("cover_prev_code")
        batch.drop_column("cover_of_id")
