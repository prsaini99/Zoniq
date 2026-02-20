# AdminActivityLog model -- audit trail for all administrative actions taken in the system
import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


# Enum defining all trackable administrative actions, organized by domain
class AdminAction(str, Enum):
    # User management actions
    BLOCK_USER = "block_user"
    UNBLOCK_USER = "unblock_user"
    MAKE_ADMIN = "make_admin"
    REMOVE_ADMIN = "remove_admin"
    DELETE_USER = "delete_user"

    # Event management actions (for future phases)
    CREATE_EVENT = "create_event"
    UPDATE_EVENT = "update_event"
    DELETE_EVENT = "delete_event"
    PUBLISH_EVENT = "publish_event"
    CANCEL_EVENT = "cancel_event"

    # Booking management actions (for future phases)
    CANCEL_BOOKING = "cancel_booking"
    REFUND_PAYMENT = "refund_payment"

    # Venue management actions (for future phases)
    CREATE_VENUE = "create_venue"
    UPDATE_VENUE = "update_venue"
    DELETE_VENUE = "delete_venue"

    # Seat management actions (for future phases)
    RELEASE_SEAT = "release_seat"


# Database model for the admin activity log
# Records every administrative action for auditing, compliance, and debugging
# Each log entry captures who did what, to which entity, and from where
class AdminActivityLog(Base):  # type: ignore
    __tablename__ = "admin_activity_log"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    # Foreign key to the admin who performed the action; SET NULL if the admin account is deleted
    admin_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("account.id", ondelete="SET NULL"), nullable=True
    )
    # The action that was performed (e.g., "block_user", "create_event")
    action: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=100), nullable=False)
    # The type of entity the action was performed on (e.g., "account", "event", "venue")
    entity_type: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=50), nullable=True)
    # The ID of the specific entity that was acted upon
    entity_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(sqlalchemy.Integer, nullable=True)
    # JSON field for additional context about the action (e.g., old/new values, reason)
    details: SQLAlchemyMapped[dict | None] = sqlalchemy_mapped_column(sqlalchemy.JSON, nullable=True)
    # IP address of the admin at the time of the action, for security auditing
    ip_address: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=45), nullable=True)
    # When the action was performed
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}
