# NotificationPreference model -- stores per-user email notification opt-in/opt-out settings
import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


# Database model for user notification preferences
# Each user has exactly one row (enforced by unique constraint on user_id)
# Controls which types of email notifications the user receives
class NotificationPreference(Base):
    __tablename__ = "notification_preference"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    # Foreign key to the user's account; unique ensures one preference record per user
    # Cascades on user deletion so preferences are removed when the account is deleted
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Email notification preferences
    # Whether to send email when a booking is confirmed
    email_booking_confirmation: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    # Whether to send email for payment status updates (success, failure, refund)
    email_payment_updates: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    # Whether to send email with ticket delivery (e-tickets, QR codes)
    email_ticket_delivery: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    # Whether to send reminder emails before the event date
    email_event_reminders: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    # Whether to send emails about changes to events the user has booked (venue change, time change, etc.)
    email_event_updates: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    # Whether to send emails about ticket transfer activity (incoming/outgoing transfers)
    email_transfer_notifications: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    # Whether to send promotional/marketing emails; defaults to False (opt-in only)
    email_marketing: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )

    # When the preference record was created
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )
    # When the preference record was last updated; auto-populated on row update by the database
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=True,
        server_onupdate=sqlalchemy.schema.FetchedValue(for_update=True),
    )

    # Relationships
    # One-to-one: links back to the user's account; eager-loaded via JOIN
    # Uses backref to make notification_preferences accessible from the Account model
    user = relationship("Account", backref="notification_preferences", lazy="joined")

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}
