# Wishlist model -- allows users to save events they are interested in for later
"""
Wishlist Database Model
"""
import datetime

import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


# Database model for wishlist entries
# Links a user (account) to an event they want to track or bookmark
# A user can only add the same event once (enforced by unique constraint)
class Wishlist(Base):
    __tablename__ = "wishlist"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Foreign key to the user's account; cascades on user deletion; indexed for fast lookups
    account_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Foreign key to the event being wishlisted; cascades on event deletion; indexed for fast lookups
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        ForeignKey("event.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # When the event was added to the wishlist
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime.now(datetime.timezone.utc),
    )

    # Relationships
    # Many-to-one: each wishlist entry belongs to one account
    account = relationship("Account", back_populates="wishlist_items")
    # Many-to-one: each wishlist entry references one event
    event = relationship("Event", back_populates="wishlist_items")

    # Unique constraint to prevent duplicate entries
    # Ensures a user cannot add the same event to their wishlist more than once
    __table_args__ = (
        sqlalchemy.UniqueConstraint("account_id", "event_id", name="uq_wishlist_account_event"),
    )

    def __repr__(self) -> str:
        return f"<Wishlist(id={self.id}, account_id={self.account_id}, event_id={self.event_id})>"
