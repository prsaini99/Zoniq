# TicketTransfer model -- tracks the transfer of tickets between users
import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


# Database model for ticket transfers between users
# Supports transfers to both registered users (via user ID) and unregistered users (via email + token)
class TicketTransfer(Base):
    """
    Tracks ticket transfer history between users.
    """
    __tablename__ = "ticket_transfer"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # The ticket being transferred
    # Foreign key to the specific booking item (ticket) being transferred
    booking_item_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("booking_item.id", ondelete="CASCADE"), nullable=False
    )
    # Original owner
    # Foreign key to the account of the user sending the ticket
    from_user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    # New owner (if registered user)
    # Foreign key to the receiving user's account; NULL if the recipient is not yet registered
    to_user_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="SET NULL"), nullable=True
    )
    # Email of recipient (for unregistered users or pending transfers)
    # Used to send the transfer claim link via email
    to_email: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=False
    )
    # Transfer token for claiming (sent via email)
    # Unique token included in the claim URL; recipient uses this to accept the transfer
    transfer_token: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True, unique=True
    )
    # Status: pending, completed, cancelled, expired
    # Lifecycle status of the transfer
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="pending"
    )
    # Optional message from sender
    # Personal message attached by the sender (e.g., "Enjoy the show!")
    message: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # Timestamps
    # When the transfer was initiated
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    # Deadline by which the recipient must claim the transfer before it expires
    expires_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
    )
    # When the transfer was successfully completed (ticket claimed by recipient)
    transferred_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # When the transfer was cancelled by the sender
    cancelled_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Indexes for common lookups: by ticket, sender, recipient, token, and status
    __table_args__ = (
        sqlalchemy.Index("ix_ticket_transfer_item", "booking_item_id"),
        sqlalchemy.Index("ix_ticket_transfer_from", "from_user_id"),
        sqlalchemy.Index("ix_ticket_transfer_to", "to_user_id"),
        sqlalchemy.Index("ix_ticket_transfer_token", "transfer_token"),
        sqlalchemy.Index("ix_ticket_transfer_status", "status"),
    )

    # Relationships
    # Many-to-one: the booking item (ticket) being transferred; eager-loaded via JOIN
    booking_item = relationship("BookingItem", lazy="joined")
    # Many-to-one: the sender of the ticket; eager-loaded, disambiguated by foreign key
    from_user = relationship("Account", foreign_keys=[from_user_id], lazy="joined")
    # Many-to-one: the recipient of the ticket; eager-loaded, disambiguated by foreign key
    to_user = relationship("Account", foreign_keys=[to_user_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<TicketTransfer(id={self.id}, item={self.booking_item_id}, status='{self.status}')>"
