# Event model -- represents a bookable event (concert, sports match, conference, etc.)
import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON, TSVECTOR

from src.repository.table import Base


# Enum for the lifecycle status of an event
class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    SOLDOUT = "soldout"


# Enum for event categories used for filtering and display
class EventCategory(str, Enum):
    CONCERT = "concert"
    SPORTS = "sports"
    THEATER = "theater"
    COMEDY = "comedy"
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    FESTIVAL = "festival"
    EXHIBITION = "exhibition"
    OTHER = "other"


# Database model for events, storing all event details, scheduling, capacity, and queue settings
class Event(Base):
    __tablename__ = "event"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Display title of the event
    title: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=False
    )
    # URL-friendly slug derived from the title, must be unique across all events
    slug: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=300), nullable=False, unique=True
    )
    # Full event description, supports long-form text
    description: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )
    # Brief summary shown in event listings and cards
    short_description: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # Category of the event (concert, sports, etc.), defaults to "other"
    category: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=False, default=EventCategory.OTHER.value
    )
    # Venue relationship
    # Foreign key to the venue where this event takes place; set to NULL if venue is deleted
    venue_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("venue.id", ondelete="SET NULL"), nullable=True
    )
    # Event timing
    # Start date and time of the event (timezone-aware)
    event_date: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    # Optional end date for multi-day or extended events
    event_end_date: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Booking window
    # When ticket sales open for this event
    booking_start_date: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    # When ticket sales close for this event
    booking_end_date: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    # Status
    # Current lifecycle status of the event (draft, published, cancelled, etc.)
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default=EventStatus.DRAFT.value
    )
    # Images
    # URL for the large banner image displayed on the event detail page
    banner_image_url: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # URL for the smaller thumbnail image shown in event listings
    thumbnail_image_url: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # Additional info
    # Terms and conditions that users must agree to before booking
    terms_and_conditions: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )
    # Organizer info
    # Name of the event organizer or organization
    organizer_name: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    # Contact info (email or phone) for the event organizer
    organizer_contact: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    # Booking settings
    # Maximum number of tickets a single user can purchase in one booking
    max_tickets_per_booking: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=10
    )
    # Total capacity (sum of all seat categories)
    # Total number of seats/tickets for this event across all categories
    total_seats: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    # Number of seats still available for purchase; decremented on booking
    available_seats: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    # Extra data (for flexible additional data)
    # JSON field for storing arbitrary key-value data (e.g., custom attributes, metadata)
    extra_data: SQLAlchemyMapped[dict | None] = sqlalchemy_mapped_column(
        JSON, nullable=True
    )
    # Full-text search vector (auto-populated by trigger)
    # PostgreSQL TSVECTOR column for efficient full-text search on title/description
    search_vector = sqlalchemy_mapped_column(
        TSVECTOR, nullable=True
    )
    # Queue settings (for high-demand events)
    # Whether a virtual queue is enabled for this event to manage high demand
    queue_enabled: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )
    # Number of users processed per batch when the queue is active
    queue_batch_size: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=50
    )
    # Time in minutes each batch has to complete checkout before the next batch is processed
    queue_processing_minutes: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=10
    )
    # Audit fields
    # Foreign key to the admin account that created this event; set NULL on admin deletion
    created_by: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="SET NULL"), nullable=True
    )
    # Timestamps
    # When the event record was created in the database
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    # When the event record was last updated
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # When the event was published (made visible to users)
    published_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # When the event was cancelled, if applicable
    cancelled_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Relationships (loaded lazily by default)
    # Many-to-one: each event belongs to one venue; eager-loaded via JOIN for performance
    venue = relationship("Venue", lazy="joined")
    # One-to-many: wishlist entries referencing this event; cascade deletes on event removal
    wishlist_items = relationship("Wishlist", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title='{self.title}', status='{self.status}')>"

    # Returns True if the event is published and the current time falls within the booking window
    @property
    def is_booking_open(self) -> bool:
        """Check if booking is currently open for this event"""
        now = datetime.datetime.now(datetime.timezone.utc)
        return (
            self.status == EventStatus.PUBLISHED.value
            and self.booking_start_date <= now <= self.booking_end_date
        )

    # Returns True if no seats remain for this event
    @property
    def is_soldout(self) -> bool:
        """Check if event is sold out"""
        return self.available_seats <= 0
