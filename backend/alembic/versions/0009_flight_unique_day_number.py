"""one flight leg per day + FLT number (review B5)

An Excel import with two rows for the same day + FLT stored two legs; the
manual upsert then failed (500) and every later import failed (422). Existing
duplicates are removed first, keeping the lowest id per (day, flt_number) —
flight pairs are derived from the set of FLT numbers, so ``flight_days`` stays
correct — then the unique constraint is added.

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-08
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CONSTRAINT = "uq_flights_day_flt_number"


def upgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM flights WHERE id NOT IN ("
            "SELECT keep_id FROM ("
            "SELECT MIN(id) AS keep_id FROM flights GROUP BY day, flt_number"
            ") AS keepers)"
        )
    )
    # Batch mode so SQLite (no ALTER TABLE ADD CONSTRAINT) recreates the table;
    # PostgreSQL gets a plain ALTER TABLE.
    with op.batch_alter_table("flights") as batch:
        batch.create_unique_constraint(_CONSTRAINT, ["day", "flt_number"])


def downgrade() -> None:
    with op.batch_alter_table("flights") as batch:
        batch.drop_constraint(_CONSTRAINT, type_="unique")
