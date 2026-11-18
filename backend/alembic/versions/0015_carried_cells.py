"""a month's roster runs to the end of its last week: carried cells

Generating a month also plans the next month's days up to the Sunday that
ends the month's last week (owner 2026-11-18). Those cells live in the next
month's schedule, marked ``carried``; generating that month keeps them as
they are. Existing cells are ordinary ones (false).

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("shift_assignments") as batch:
        batch.add_column(
            sa.Column("carried", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("shift_assignments") as batch:
        batch.drop_column("carried")
