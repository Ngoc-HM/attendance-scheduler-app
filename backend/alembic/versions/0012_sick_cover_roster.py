"""remember the roster cell a sick cover replaced

The A/D sick cover now also goes into the colleague's roster cell (owner
2026-11-13: the published roster is the person's schedule, so they see the
cover there). ``cover_prev_plan_code`` / ``cover_prev_plan_override`` keep
that roster cell as it was, so taking the S back restores it too.

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Stored labels are the enum member names (see 0001).
_CODES = ("A", "D", "A_D", "AD", "X", "CD", "O_D", "T", "B", "S", "AL")


def upgrade() -> None:
    with op.batch_alter_table("attendance_records") as batch:
        batch.add_column(
            sa.Column(
                "cover_prev_plan_code",
                sa.Enum(*_CODES, name="attendance_code", create_type=False),
                nullable=True,
            )
        )
        batch.add_column(
            sa.Column(
                "cover_prev_plan_override",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("attendance_records") as batch:
        batch.drop_column("cover_prev_plan_override")
        batch.drop_column("cover_prev_plan_code")
