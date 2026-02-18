import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


class AdminAction(str, Enum):
    # User actions
    BLOCK_USER = "block_user"
    UNBLOCK_USER = "unblock_user"
    MAKE_ADMIN = "make_admin"
    REMOVE_ADMIN = "remove_admin"
    DELETE_USER = "delete_user"

    # Event actions (for future phases)
    CREATE_EVENT = "create_event"
    UPDATE_EVENT = "update_event"
    DELETE_EVENT = "delete_event"
    PUBLISH_EVENT = "publish_event"
    CANCEL_EVENT = "cancel_event"

    # Booking actions (for future phases)
    CANCEL_BOOKING = "cancel_booking"
    REFUND_PAYMENT = "refund_payment"

    # Venue actions (for future phases)
    CREATE_VENUE = "create_venue"
    UPDATE_VENUE = "update_venue"
    DELETE_VENUE = "delete_venue"

    # Seat actions (for future phases)
    RELEASE_SEAT = "release_seat"


class AdminActivityLog(Base):  # type: ignore
    __tablename__ = "admin_activity_log"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    admin_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("account.id", ondelete="SET NULL"), nullable=True
    )
    action: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=100), nullable=False)
    entity_type: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=50), nullable=True)
    entity_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(sqlalchemy.Integer, nullable=True)
    details: SQLAlchemyMapped[dict | None] = sqlalchemy_mapped_column(sqlalchemy.JSON, nullable=True)
    ip_address: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=45), nullable=True)
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )

    __mapper_args__ = {"eager_defaults": True}
