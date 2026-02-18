import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


class TicketTransfer(Base):
    """
    Tracks ticket transfer history between users.
    """
    __tablename__ = "ticket_transfer"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # The ticket being transferred
    booking_item_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("booking_item.id", ondelete="CASCADE"), nullable=False
    )
    # Original owner
    from_user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    # New owner (if registered user)
    to_user_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="SET NULL"), nullable=True
    )
    # Email of recipient (for unregistered users or pending transfers)
    to_email: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=False
    )
    # Transfer token for claiming (sent via email)
    transfer_token: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True, unique=True
    )
    # Status: pending, completed, cancelled, expired
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="pending"
    )
    # Optional message from sender
    message: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # Timestamps
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    expires_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
    )
    transferred_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    cancelled_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    __mapper_args__ = {"eager_defaults": True}

    __table_args__ = (
        sqlalchemy.Index("ix_ticket_transfer_item", "booking_item_id"),
        sqlalchemy.Index("ix_ticket_transfer_from", "from_user_id"),
        sqlalchemy.Index("ix_ticket_transfer_to", "to_user_id"),
        sqlalchemy.Index("ix_ticket_transfer_token", "transfer_token"),
        sqlalchemy.Index("ix_ticket_transfer_status", "status"),
    )

    # Relationships
    booking_item = relationship("BookingItem", lazy="joined")
    from_user = relationship("Account", foreign_keys=[from_user_id], lazy="joined")
    to_user = relationship("Account", foreign_keys=[to_user_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<TicketTransfer(id={self.id}, item={self.booking_item_id}, status='{self.status}')>"
