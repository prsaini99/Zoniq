import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


class OTPPurpose(str, Enum):
    LOGIN = "login"
    VERIFY_PHONE = "verify_phone"
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"
    EMAIL_LOGIN = "email_login"


class OTPCode(Base):  # type: ignore
    __tablename__ = "otp_code"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    user_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=True
    )
    phone: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=20), nullable=True)
    email: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=255), nullable=True)
    code: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=10), nullable=False)
    purpose: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=50), nullable=False)
    expires_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    is_used: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )

    __mapper_args__ = {"eager_defaults": True}

    @property
    def is_expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
