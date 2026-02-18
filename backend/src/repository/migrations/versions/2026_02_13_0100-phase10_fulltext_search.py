"""Add full-text search for events

Revision ID: phase10_fulltext_search
Revises: phase9_queue_system
Create Date: 2026-02-13 01:00:00.000000

This migration adds:
- search_vector column (TSVECTOR) to event table
- GIN index for fast full-text search
- Trigger function to auto-update search_vector on INSERT/UPDATE
- Populates existing events with search vectors
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR


# revision identifiers, used by Alembic.
revision = 'phase10_fulltext_search'
down_revision = 'phase9_queue_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add search_vector column
    op.add_column('event', sa.Column('search_vector', TSVECTOR, nullable=True))

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX ix_event_search_vector ON event USING GIN (search_vector)
    """)

    # Create trigger function to auto-update search_vector
    op.execute("""
        CREATE OR REPLACE FUNCTION event_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', COALESCE(NEW.short_description, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.organizer_name, '')), 'B') ||
                setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to call the function on INSERT or UPDATE
    op.execute("""
        CREATE TRIGGER event_search_vector_trigger
        BEFORE INSERT OR UPDATE OF title, short_description, description, organizer_name
        ON event
        FOR EACH ROW
        EXECUTE FUNCTION event_search_vector_update();
    """)

    # Populate search_vector for existing events
    op.execute("""
        UPDATE event SET search_vector =
            setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(short_description, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(organizer_name, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(description, '')), 'C');
    """)


def downgrade() -> None:
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS event_search_vector_trigger ON event")

    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS event_search_vector_update()")

    # Drop index
    op.execute("DROP INDEX IF EXISTS ix_event_search_vector")

    # Drop column
    op.drop_column('event', 'search_vector')
