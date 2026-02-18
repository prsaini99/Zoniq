import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


class Payment(Base):
    """
    Payment record tracking Razorpay transactions.
    """
    __tablename__ = "payment"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Link to booking
    booking_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("booking.id", ondelete="CASCADE"), nullable=False
    )
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    # Razorpay IDs
    razorpay_order_id: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=False, unique=True
    )
    razorpay_payment_id: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True
    )
    razorpay_signature: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # Amount in paise (smallest currency unit)
    amount: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    currency: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=10), nullable=False, default="INR"
    )
    # Status
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="created"
    )  # created, authorized, captured, failed, refunded
    # Payment method details
    method: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )  # card, upi, netbanking, wallet
    # Error tracking
    error_code: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True
    )
    error_description: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # Refund tracking
    refund_id: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=True
    )
    refund_amount: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    refund_status: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )  # pending, processed, failed
    # Timestamps
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    paid_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    refunded_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    __mapper_args__ = {"eager_defaults": True}

    __table_args__ = (
        sqlalchemy.Index("ix_payment_booking", "booking_id"),
        sqlalchemy.Index("ix_payment_user", "user_id"),
        sqlalchemy.Index("ix_payment_order_id", "razorpay_order_id"),
        sqlalchemy.Index("ix_payment_status", "status"),
    )

    # Relationships
    booking = relationship("Booking", lazy="joined")
    user = relationship("Account", lazy="joined")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, order_id='{self.razorpay_order_id}', status='{self.status}')>"
