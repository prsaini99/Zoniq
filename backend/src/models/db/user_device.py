import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.repository.table import Base


class UserDevice(Base):  # type: ignore
    __tablename__ = "user_device"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(primary_key=True, autoincrement="auto")
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    device_fingerprint: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=500), nullable=True
    )
    ip_address: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=45), nullable=True)
    user_agent: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.Text, nullable=True)
    browser: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=100), nullable=True)
    os: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(sqlalchemy.String(length=100), nullable=True)
    is_trusted: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(sqlalchemy.Boolean, nullable=False, default=False)
    last_seen_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False, server_default=sqlalchemy_functions.now()
    )

    __mapper_args__ = {"eager_defaults": True}
