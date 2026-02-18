import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class Account(Base):  # type: ignore
    __tablename__ = "account"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    username: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=64), nullable=False, unique=True
    )
    email: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=64), nullable=False, unique=True)
    _hashed_password: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=1024), nullable=True)
    _hash_salt: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(sqlalchemy.String(length=1024), nullable=True)

    # New fields for Phase 1
    role: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=20), nullable=False, default=UserRole.USER.value
    )
    phone: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=20), nullable=True)
    full_name: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=255), nullable=True)
    is_phone_verified: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )
    is_blocked: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    blocked_reason: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.Text, nullable=True)
    last_login_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Existing fields
    is_verified: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    is_active: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    is_logged_in: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )
    updated_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=True,
        server_onupdate=sqlalchemy.schema.FetchedValue(for_update=True),
    )

    __mapper_args__ = {"eager_defaults": True}

    # Relationships
    wishlist_items = relationship("Wishlist", back_populates="account", cascade="all, delete-orphan")

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    def set_hashed_password(self, hashed_password: str) -> None:
        self._hashed_password = hashed_password

    @property
    def hash_salt(self) -> str:
        return self._hash_salt

    def set_hash_salt(self, hash_salt: str) -> None:
        self._hash_salt = hash_salt

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value
