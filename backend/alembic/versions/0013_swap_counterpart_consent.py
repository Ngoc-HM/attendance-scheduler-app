"""a swap needs the colleague's consent before the admin decides

``counterpart_status`` is the colleague's own answer to a ``swap_with``
request: pending until they accept (approved) or decline (rejected); NULL
for a code change. Existing swaps: an approved one counts as accepted, a
pending one now waits for the colleague.

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    status = sa.Enum("pending", "approved", "rejected", name="leave_status", create_type=False)
    with op.batch_alter_table("shift_change_requests") as batch:
        batch.add_column(sa.Column("counterpart_status", status, nullable=True))
        batch.add_column(sa.Column("counterpart_decided_at", sa.DateTime(), nullable=True))
    op.execute(
        "UPDATE shift_change_requests SET counterpart_status = 'approved' "
        "WHERE kind = 'swap_with' AND status = 'approved'"
    )
    op.execute(
        "UPDATE shift_change_requests SET counterpart_status = 'pending' "
        "WHERE kind = 'swap_with' AND status = 'pending'"
    )


def downgrade() -> None:
    with op.batch_alter_table("shift_change_requests") as batch:
        batch.drop_column("counterpart_decided_at")
        batch.drop_column("counterpart_status")
