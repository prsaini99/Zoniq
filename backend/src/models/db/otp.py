# OTPCode model -- stores one-time passwords for phone/email verification and passwordless login
import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


# Enum defining the different purposes an OTP can serve
class OTPPurpose(str, Enum):
    LOGIN = "login"                    # OTP-based phone login
    VERIFY_PHONE = "verify_phone"      # Verify phone number ownership
    VERIFY_EMAIL = "verify_email"      # Verify email address ownership
    RESET_PASSWORD = "reset_password"  # Password reset flow
    EMAIL_LOGIN = "email_login"        # OTP-based email login


# Database model for one-time password codes
# OTPs are short-lived codes sent via SMS or email for authentication and verification
class OTPCode(Base):  # type: ignore
    __tablename__ = "otp_code"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    # Foreign key to the user's account; nullable for cases where the user is not yet registered
    # Cascades on user deletion
    user_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=True
    )
    # Phone number the OTP was sent to (for phone-based OTPs)
    phone: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=20), nullable=True)
    # Email address the OTP was sent to (for email-based OTPs)
    email: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=255), nullable=True)
    # The actual OTP code (e.g., "123456"), stored as a string to preserve leading zeros
    code: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=10), nullable=False)
    # Purpose of this OTP (login, verify_phone, verify_email, reset_password, email_login)
    purpose: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=50), nullable=False)
    # Expiration timestamp; the OTP becomes invalid after this time
    expires_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    # Whether the OTP has already been consumed; prevents reuse
    is_used: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    # When the OTP was created and sent
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Returns True if the current time is past the OTP's expiration
    @property
    def is_expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at

    # Returns True if the OTP has not been used and has not expired (still valid for verification)
    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
