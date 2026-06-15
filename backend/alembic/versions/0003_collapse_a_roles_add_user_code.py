"""collapse A1-A4 roles → A, add users.code, add role_code_counters table

- Collapses role enum from {M,T,A1,A2,A3,A4} to {M,T,A}:
  all Ax variants map to 'A' via CASE WHEN on Postgres; data UPDATE on SQLite.
- Adds role_code_counters table for monotonic never-reused per-role code counters.
- Adds users.code column (String(8)), backfills existing rows ordered by id
  (numbering from 1 per role letter), then makes it NOT NULL + unique indexed.
- Seeds role_code_counters.next_seq to the max assigned seq per role.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-15
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # ------------------------------------------------------------------
    # 1. Create role_code_counters table
    # ------------------------------------------------------------------
    op.create_table(
        "role_code_counters",
        sa.Column("role", sa.String(2), primary_key=True),
        sa.Column("next_seq", sa.Integer(), nullable=False, server_default="0"),
    )

    # ------------------------------------------------------------------
    # 2. Add users.code as nullable first (so existing rows don't break)
    # ------------------------------------------------------------------
    op.add_column("users", sa.Column("code", sa.String(8), nullable=True))

    # ------------------------------------------------------------------
    # 3. Collapse A1-A4 → A in the users.role column
    # ------------------------------------------------------------------
    if is_pg:
        # Postgres: rename old enum, create new 3-value enum, alter column.
        bind.execute(sa.text("ALTER TYPE role RENAME TO role_old"))
        bind.execute(sa.text("CREATE TYPE role AS ENUM ('M', 'T', 'A')"))
        bind.execute(sa.text(
            "ALTER TABLE users ALTER COLUMN role TYPE role "
            "USING (CASE WHEN role::text LIKE 'A%' THEN 'A' ELSE role::text END)::role"
        ))
        bind.execute(sa.text("DROP TYPE role_old"))
    else:
        # SQLite has no real enum type; just update the data values.
        bind.execute(sa.text(
            "UPDATE users SET role = 'A' WHERE role IN ('A1','A2','A3','A4')"
        ))

    # ------------------------------------------------------------------
    # 4. Backfill users.code grouped by role letter, ordered by id
    # ------------------------------------------------------------------
    # Fetch all users ordered by id so each role group gets seq 1,2,3...
    result = bind.execute(
        sa.text("SELECT id, role FROM users ORDER BY id")
    ).fetchall()

    # Track per-role counter locally for backfill
    role_seq: dict[str, int] = {}
    for row in result:
        user_id, role_val = row[0], row[1]
        # After the collapse above, role is now one of M/T/A
        role_letter = role_val  # already collapsed
        role_seq[role_letter] = role_seq.get(role_letter, 0) + 1
        code = f"{role_letter}{role_seq[role_letter]}"
        bind.execute(
            sa.text("UPDATE users SET code = :code WHERE id = :id"),
            {"code": code, "id": user_id},
        )

    # ------------------------------------------------------------------
    # 5. Seed role_code_counters with max seq per role
    # ------------------------------------------------------------------
    for role_letter, max_seq in role_seq.items():
        bind.execute(
            sa.text(
                "INSERT INTO role_code_counters (role, next_seq) VALUES (:role, :seq)"
            ),
            {"role": role_letter, "seq": max_seq},
        )

    # ------------------------------------------------------------------
    # 6. Make users.code NOT NULL and add unique index
    # ------------------------------------------------------------------
    if is_pg:
        bind.execute(sa.text("ALTER TABLE users ALTER COLUMN code SET NOT NULL"))
    else:
        # SQLite does not support ALTER COLUMN; recreate the column constraint
        # via batch migration.
        with op.batch_alter_table("users") as batch_op:
            batch_op.alter_column("code", nullable=False)

    op.create_index("ix_users_code", "users", ["code"], unique=True)


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade from 0003 is not supported: the collapsed role enum "
        "and code assignments cannot be deterministically reversed."
    )
