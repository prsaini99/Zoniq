import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preference"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Email notification preferences
    email_booking_confirmation: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    email_payment_updates: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    email_ticket_delivery: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    email_event_reminders: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    email_event_updates: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    email_transfer_notifications: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    email_marketing: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )

    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=True,
        server_onupdate=sqlalchemy.schema.FetchedValue(for_update=True),
    )

    # Relationships
    user = relationship("Account", backref="notification_preferences", lazy="joined")

    __mapper_args__ = {"eager_defaults": True}
