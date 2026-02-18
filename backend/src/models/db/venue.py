import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column
from sqlalchemy.dialects.postgresql import JSON

from src.repository.table import Base


class Venue(Base):
    __tablename__ = "venue"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    name: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=False
    )
    address: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )
    city: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True
    )
    state: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True
    )
    country: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True, default="India"
    )
    pincode: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=20), nullable=True
    )
    capacity: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    # Flexible seat layout configuration (rows, sections, etc.)
    seat_map_config: SQLAlchemyMapped[dict | None] = sqlalchemy_mapped_column(
        JSON, nullable=True
    )
    # Contact information
    contact_phone: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=20), nullable=True
    )
    contact_email: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    # Status
    is_active: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
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

    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, name='{self.name}', city='{self.city}')>"
