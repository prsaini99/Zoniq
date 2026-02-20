# Account model -- represents a user or admin in the ticketing platform
import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


# Enum defining the two roles a user can have in the system
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


# Database model for user accounts, storing credentials, profile info, and status flags
class Account(Base):  # type: ignore
    __tablename__ = "account"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    # Unique username for login and display, max 64 characters
    username: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=64), nullable=False, unique=True
    )
    # Unique email address for the account, used for notifications and login
    email: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=64), nullable=False, unique=True)
    # Hashed password stored securely; prefixed with underscore to discourage direct access
    _hashed_password: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=1024), nullable=True)
    # Salt used in password hashing for added security
    _hash_salt: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=1024), nullable=True)

    # New fields for Phase 1
    # Role of the user: "user" or "admin", defaults to regular user
    role: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=20), nullable=False, default=UserRole.USER.value
    )
    # Optional phone number for the user, used for OTP verification
    phone: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=20), nullable=True)
    # Optional full name of the user for display purposes
    full_name: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=255), nullable=True)
    # Whether the user's phone number has been verified via OTP
    is_phone_verified: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )
    # Whether the account has been blocked by an admin
    is_blocked: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    # Reason provided by admin for blocking the account
    blocked_reason: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.Text, nullable=True)
    # Timestamp of the user's most recent login
    last_login_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Existing fields
    # Whether the user's email has been verified
    is_verified: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    # Whether the account is active (enabled); inactive accounts cannot interact with the system
    is_active: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    # Whether the user currently has an active session
    is_logged_in: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    # Timestamp when the account was created, auto-set by the database
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )
    # Timestamp of the last update, auto-populated on row update by the database
    updated_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=True,
        server_onupdate=sqlalchemy.schema.FetchedValue(for_update=True),
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Relationships
    # One-to-many relationship with Wishlist; deleting an account removes its wishlist entries
    wishlist_items = relationship("Wishlist", back_populates="account", cascade="all, delete-orphan")

    # Property to safely read the hashed password without exposing the internal column
    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    # Setter for hashed password, used during registration and password changes
    def set_hashed_password(self, hashed_password: str) -> None:
        self._hashed_password = hashed_password

    # Property to safely read the hash salt
    @property
    def hash_salt(self) -> str:
        return self._hash_salt

    # Setter for hash salt, used alongside password hashing
    def set_hash_salt(self, hash_salt: str) -> None:
        self._hash_salt = hash_salt

    # Convenience property to check if the account holds admin privileges
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value
