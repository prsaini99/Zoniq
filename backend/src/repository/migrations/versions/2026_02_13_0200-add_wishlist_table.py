"""Add wishlist table

Revision ID: add_wishlist_table
Revises: phase10_fulltext_search
Create Date: 2026-02-13 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_wishlist_table'
down_revision = 'phase10_fulltext_search'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'wishlist',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['account_id'], ['account.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['event.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'event_id', name='uq_wishlist_account_event')
    )
    op.create_index('ix_wishlist_account_id', 'wishlist', ['account_id'], unique=False)
    op.create_index('ix_wishlist_event_id', 'wishlist', ['event_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_wishlist_event_id', table_name='wishlist')
    op.drop_index('ix_wishlist_account_id', table_name='wishlist')
    op.drop_table('wishlist')
