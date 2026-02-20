# Venue model -- represents a physical location where events are held
import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column
from sqlalchemy.dialects.postgresql import JSON

from src.repository.table import Base


# Database model for venues, storing location details, capacity, and seat layout configuration
class Venue(Base):
    __tablename__ = "venue"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Display name of the venue (e.g., "Madison Square Garden")
    name: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=False
    )
    # Full street address of the venue
    address: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )
    # City where the venue is located
    city: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True
    )
    # State or province of the venue
    state: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True
    )
    # Country of the venue, defaults to "India"
    country: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True, default="India"
    )
    # Postal/ZIP code for the venue address
    pincode: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=20), nullable=True
    )
    # Maximum seating capacity of the venue
    capacity: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    # Flexible seat layout configuration (rows, sections, etc.)
    # JSON structure defining how seats are arranged (sections, rows, numbering schemes)
    seat_map_config: SQLAlchemyMapped[dict | None] = sqlalchemy_mapped_column(
        JSON, nullable=True
    )
    # Contact information
    # Phone number for venue management or inquiries
    contact_phone: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=20), nullable=True
    )
    # Email address for venue management or inquiries
    contact_email: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    # Status
    # Whether the venue is active and available for hosting events
    is_active: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    # Timestamps
    # When the venue record was created in the database
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    # When the venue record was last updated
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, name='{self.name}', city='{self.city}')>"
