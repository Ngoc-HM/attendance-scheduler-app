"""add self_arrange_requests table (batch propose + approve, owner 2026-07-09)

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum type already exists in the database (created in 0001) — reuse.
leave_status = postgresql.ENUM(
    "pending", "approved", "rejected", name="leave_status", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "self_arrange_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("status", leave_status, nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("decided_by_id", sa.Integer(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_self_arrange_requests_requester_id",
        "self_arrange_requests",
        ["requester_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_self_arrange_requests_requester_id", table_name="self_arrange_requests"
    )
    # leave_status enum is shared with leave/shift-change tables — do not drop.
    op.drop_table("self_arrange_requests")
