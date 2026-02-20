# UserDevice model -- tracks devices that users have logged in from, for security and trust management
import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


# Database model for tracking user devices
# Records device information each time a user logs in from a new device
# Used for security (detecting suspicious logins) and device trust management
class UserDevice(Base):  # type: ignore
    __tablename__ = "user_device"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    # Foreign key to the user who owns this device record; cascades on user deletion
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    # Unique fingerprint hash identifying the device (generated client-side from device characteristics)
    device_fingerprint: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    # IP address from which the device last connected
    ip_address: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=45), nullable=True)
    # Full user-agent string from the HTTP request header
    user_agent: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.Text, nullable=True)
    # Parsed browser name (e.g., "Chrome", "Firefox", "Safari")
    browser: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=100), nullable=True)
    # Parsed operating system name (e.g., "Windows 11", "macOS", "Android")
    os: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=100), nullable=True)
    # Whether this device has been marked as trusted by the user (skips extra verification)
    is_trusted: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    # Timestamp of the most recent activity from this device; updated on each login
    last_seen_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )
    # When this device record was first created (first login from this device)
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}
