"""add users.carry_premium_off + shift_change_requests (locked decisions #6, #8)

- ``users.carry_premium_off``: premium OFF days (Sat/Sun/holiday) received so
  far, balanced across months by the premium-off fairness objective.
- ``shift_change_requests``: change-code / swap-with requests, admin-decided.
  Reuses the existing ``attendance_code`` and ``leave_status`` enum types
  (create_type=False); only ``swap_kind`` is new.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-11 20:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum type introduced by this revision.
swap_kind = postgresql.ENUM('change_code', 'swap_with', name='swap_kind',
                            create_type=False)

# Enum types that already exist in the database (created in 0001) — reuse.
attendance_code = postgresql.ENUM(
    'A', 'D', 'A_D', 'AD', 'X', 'CD', 'O_D', 'T', 'B', 'S', 'AL',
    name='attendance_code', create_type=False,
)
leave_status = postgresql.ENUM('pending', 'approved', 'rejected',
                               name='leave_status', create_type=False)


def upgrade() -> None:
    # server_default backfills existing rows; matches the ORM default of 0.
    op.add_column(
        'users',
        sa.Column('carry_premium_off', sa.Integer(), nullable=False,
                  server_default='0'),
    )

    swap_kind.create(op.get_bind(), checkfirst=True)
    op.create_table(
        'shift_change_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('kind', swap_kind, nullable=False),
        sa.Column('requested_code', attendance_code, nullable=True),
        sa.Column('counterpart_user_id', sa.Integer(), nullable=True),
        sa.Column('status', leave_status, nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('decided_by_id', sa.Integer(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False),
        sa.ForeignKeyConstraint(['counterpart_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['decided_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_shift_change_requests_requester_id'),
                    'shift_change_requests', ['requester_id'], unique=False)
    op.create_index(op.f('ix_shift_change_requests_work_date'),
                    'shift_change_requests', ['work_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_shift_change_requests_work_date'),
                  table_name='shift_change_requests')
    op.drop_index(op.f('ix_shift_change_requests_requester_id'),
                  table_name='shift_change_requests')
    op.drop_table('shift_change_requests')
    swap_kind.drop(op.get_bind(), checkfirst=True)
    op.drop_column('users', 'carry_premium_off')
