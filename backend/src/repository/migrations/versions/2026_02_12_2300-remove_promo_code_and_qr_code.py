"""Remove promo code system and qr_code_data

Revision ID: remove_promo_qr
Revises: 80d512d7a93e
Create Date: 2026-02-12 23:00:00.000000

This migration removes:
- qr_code_data column from booking_item table
- promo_code_id column from booking table (keeps promo_code_used for historical records)
- promo_code_id column from cart table
- promo_code table entirely
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_promo_qr'
down_revision = '80d512d7a93e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop qr_code_data column from booking_item
    op.drop_column('booking_item', 'qr_code_data')

    # Drop promo_code_id FK and column from booking
    op.drop_constraint('booking_promo_code_id_fkey', 'booking', type_='foreignkey')
    op.drop_column('booking', 'promo_code_id')

    # Drop promo_code_id FK and column from cart
    op.drop_constraint('cart_promo_code_id_fkey', 'cart', type_='foreignkey')
    op.drop_column('cart', 'promo_code_id')

    # Drop promo_code table
    op.drop_index('ix_promo_code_event', table_name='promo_code')
    op.drop_index('ix_promo_code_code', table_name='promo_code')
    op.drop_table('promo_code')


def downgrade() -> None:
    # Recreate promo_code table
    op.create_table('promo_code',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_type', sa.String(length=20), nullable=False),
        sa.Column('discount_value', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('min_purchase', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('max_discount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('usage_limit', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['event.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_promo_code_code', 'promo_code', ['code'], unique=False)
    op.create_index('ix_promo_code_event', 'promo_code', ['event_id'], unique=False)

    # Add promo_code_id column back to cart
    op.add_column('cart', sa.Column('promo_code_id', sa.Integer(), nullable=True))
    op.create_foreign_key('cart_promo_code_id_fkey', 'cart', 'promo_code', ['promo_code_id'], ['id'], ondelete='SET NULL')

    # Add promo_code_id column back to booking
    op.add_column('booking', sa.Column('promo_code_id', sa.Integer(), nullable=True))
    op.create_foreign_key('booking_promo_code_id_fkey', 'booking', 'promo_code', ['promo_code_id'], ['id'], ondelete='SET NULL')

    # Add qr_code_data column back to booking_item
    op.add_column('booking_item', sa.Column('qr_code_data', sa.String(length=500), nullable=True))
