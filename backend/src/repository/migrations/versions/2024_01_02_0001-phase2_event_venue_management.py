"""Phase 2: Event & Venue Management

Revision ID: phase2_event_venue
Revises: phase1_user_management
Create Date: 2024-01-02 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase2_event_venue'
down_revision = 'phase1_user_mgmt'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create venue table
    op.create_table(
        'venue',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True, default='India'),
        sa.Column('pincode', sa.String(length=20), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('seat_map_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amenities', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_venue_name', 'venue', ['name'], unique=False)
    op.create_index('ix_venue_city', 'venue', ['city'], unique=False)
    op.create_index('ix_venue_is_active', 'venue', ['is_active'], unique=False)

    # Create event table
    op.create_table(
        'event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=300), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False, default='other'),
        sa.Column('venue_id', sa.Integer(), sa.ForeignKey('venue.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('booking_start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('booking_end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, default='draft'),
        sa.Column('banner_image_url', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_image_url', sa.String(length=500), nullable=True),
        sa.Column('terms_and_conditions', sa.Text(), nullable=True),
        sa.Column('organizer_name', sa.String(length=255), nullable=True),
        sa.Column('organizer_contact', sa.String(length=255), nullable=True),
        sa.Column('max_tickets_per_booking', sa.Integer(), nullable=False, default=10),
        sa.Column('total_seats', sa.Integer(), nullable=False, default=0),
        sa.Column('available_seats', sa.Integer(), nullable=False, default=0),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('account.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_event_slug', 'event', ['slug'], unique=True)
    op.create_index('ix_event_status', 'event', ['status'], unique=False)
    op.create_index('ix_event_category', 'event', ['category'], unique=False)
    op.create_index('ix_event_event_date', 'event', ['event_date'], unique=False)
    op.create_index('ix_event_venue_id', 'event', ['venue_id'], unique=False)

    # Create seat_category table
    op.create_table(
        'seat_category',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_seats', sa.Integer(), nullable=False),
        sa.Column('available_seats', sa.Integer(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('color_code', sa.String(length=10), nullable=True, default='#3B82F6'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seat_category_event_id', 'seat_category', ['event_id'], unique=False)
    op.create_index('ix_seat_category_is_active', 'seat_category', ['is_active'], unique=False)

    # Create seat table
    op.create_table(
        'seat',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('seat_category.id', ondelete='CASCADE'), nullable=False),
        sa.Column('seat_number', sa.String(length=20), nullable=True),
        sa.Column('row_name', sa.String(length=10), nullable=True),
        sa.Column('section', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='available'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_by', sa.Integer(), sa.ForeignKey('account.id', ondelete='SET NULL'), nullable=True),
        sa.Column('booking_id', sa.Integer(), nullable=True),  # FK will be added in Phase 3
        sa.Column('position_x', sa.Integer(), nullable=True),
        sa.Column('position_y', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_seat_event_id', 'seat', ['event_id'], unique=False)
    op.create_index('ix_seat_category_id', 'seat', ['category_id'], unique=False)
    op.create_index('ix_seat_status', 'seat', ['status'], unique=False)
    op.create_index('ix_seat_locked_until', 'seat', ['locked_until'], unique=False)
    # Unique constraint for seat number within event
    op.create_unique_constraint('uq_seat_event_row_number', 'seat', ['event_id', 'row_name', 'seat_number'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_constraint('uq_seat_event_row_number', 'seat', type_='unique')
    op.drop_index('ix_seat_locked_until', table_name='seat')
    op.drop_index('ix_seat_status', table_name='seat')
    op.drop_index('ix_seat_category_id', table_name='seat')
    op.drop_index('ix_seat_event_id', table_name='seat')
    op.drop_table('seat')

    op.drop_index('ix_seat_category_is_active', table_name='seat_category')
    op.drop_index('ix_seat_category_event_id', table_name='seat_category')
    op.drop_table('seat_category')

    op.drop_index('ix_event_venue_id', table_name='event')
    op.drop_index('ix_event_event_date', table_name='event')
    op.drop_index('ix_event_category', table_name='event')
    op.drop_index('ix_event_status', table_name='event')
    op.drop_index('ix_event_slug', table_name='event')
    op.drop_table('event')

    op.drop_index('ix_venue_is_active', table_name='venue')
    op.drop_index('ix_venue_city', table_name='venue')
    op.drop_index('ix_venue_name', table_name='venue')
    op.drop_table('venue')
