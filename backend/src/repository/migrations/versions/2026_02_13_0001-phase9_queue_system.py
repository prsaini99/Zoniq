"""Add queue system for high-demand events

Revision ID: phase9_queue_system
Revises: remove_promo_qr
Create Date: 2026-02-13 00:01:00.000000

This migration adds:
- queue_enabled, queue_batch_size, queue_processing_minutes to event table
- queue_entry table for managing event queues
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'phase9_queue_system'
down_revision = 'remove_promo_qr'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add queue configuration columns to event table
    op.add_column('event', sa.Column('queue_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('event', sa.Column('queue_batch_size', sa.Integer(), nullable=False, server_default='50'))
    op.add_column('event', sa.Column('queue_processing_minutes', sa.Integer(), nullable=False, server_default='10'))

    # Create queue_entry table
    op.create_table('queue_entry',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='waiting'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['event.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['account.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient queue operations
    op.create_index('ix_queue_entry_event_status', 'queue_entry', ['event_id', 'status'])
    op.create_index('ix_queue_entry_event_position', 'queue_entry', ['event_id', 'position'])
    op.create_index('ix_queue_entry_user_event', 'queue_entry', ['user_id', 'event_id'])


def downgrade() -> None:
    # Drop queue_entry table indexes and table
    op.drop_index('ix_queue_entry_user_event', table_name='queue_entry')
    op.drop_index('ix_queue_entry_event_position', table_name='queue_entry')
    op.drop_index('ix_queue_entry_event_status', table_name='queue_entry')
    op.drop_table('queue_entry')

    # Remove queue configuration columns from event table
    op.drop_column('event', 'queue_processing_minutes')
    op.drop_column('event', 'queue_batch_size')
    op.drop_column('event', 'queue_enabled')
