"""patient login: password hash, login throttle, patient sessions

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-24 00:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('patient_accounts', sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.create_table('patient_login_throttles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone', sa.String(length=10), nullable=False),
    sa.Column('failed_count', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('phone')
    )
    op.create_table('patient_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['patient_accounts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_patient_sessions_account_id'), 'patient_sessions', ['account_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_patient_sessions_account_id'), table_name='patient_sessions')
    op.drop_table('patient_sessions')
    op.drop_table('patient_login_throttles')
    op.drop_column('patient_accounts', 'password_hash')
