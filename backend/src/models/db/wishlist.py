"""
Wishlist Database Model
"""
import datetime

import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


class Wishlist(Base):
    __tablename__ = "wishlist"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    account_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        ForeignKey("account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        ForeignKey("event.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        default=datetime.datetime.now(datetime.timezone.utc),
    )

    # Relationships
    account = relationship("Account", back_populates="wishlist_items")
    event = relationship("Event", back_populates="wishlist_items")

    # Unique constraint to prevent duplicate entries
    __table_args__ = (
        sqlalchemy.UniqueConstraint("account_id", "event_id", name="uq_wishlist_account_event"),
    )

    def __repr__(self) -> str:
        return f"<Wishlist(id={self.id}, account_id={self.account_id}, event_id={self.event_id})>"
