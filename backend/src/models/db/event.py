import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSON, TSVECTOR

from src.repository.table import Base


class EventStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    SOLDOUT = "soldout"


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


class Event(Base):
    __tablename__ = "event"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    title: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=False
    )
    slug: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=300), nullable=False, unique=True
    )
    description: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )
    short_description: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    category: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=False, default=EventCategory.OTHER.value
    )
    # Venue relationship
    venue_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("venue.id", ondelete="SET NULL"), nullable=True
    )
    # Event timing
    event_date: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    event_end_date: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Booking window
    booking_start_date: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    booking_end_date: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    # Status
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default=EventStatus.DRAFT.value
    )
    # Images
    banner_image_url: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    thumbnail_image_url: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # Additional info
    terms_and_conditions: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )
    # Organizer info
    organizer_name: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    organizer_contact: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    # Booking settings
    max_tickets_per_booking: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=10
    )
    # Total capacity (sum of all seat categories)
    total_seats: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    available_seats: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    # Extra data (for flexible additional data)
    extra_data: SQLAlchemyMapped[dict | None] = sqlalchemy_mapped_column(
        JSON, nullable=True
    )
    # Full-text search vector (auto-populated by trigger)
    search_vector = sqlalchemy_mapped_column(
        TSVECTOR, nullable=True
    )
    # Queue settings (for high-demand events)
    queue_enabled: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )
    queue_batch_size: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=50
    )
    queue_processing_minutes: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=10
    )
    # Audit fields
    created_by: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="SET NULL"), nullable=True
    )
    # Timestamps
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    published_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    cancelled_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    __mapper_args__ = {"eager_defaults": True}

    # Relationships (loaded lazily by default)
    venue = relationship("Venue", lazy="joined")
    wishlist_items = relationship("Wishlist", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title='{self.title}', status='{self.status}')>"

    @property
    def is_booking_open(self) -> bool:
        """Check if booking is currently open for this event"""
        now = datetime.datetime.now(datetime.timezone.utc)
        return (
            self.status == EventStatus.PUBLISHED.value
            and self.booking_start_date <= now <= self.booking_end_date
        )

    @property
    def is_soldout(self) -> bool:
        """Check if event is sold out"""
        return self.available_seats <= 0
