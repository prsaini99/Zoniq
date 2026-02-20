# Declarative base class for all SQLAlchemy ORM models.
# Every database model in the application should inherit from Base (aliased from DBTable).

import typing

import sqlalchemy
from sqlalchemy.orm import DeclarativeBase


# DBTable serves as the root declarative base, providing shared metadata for all models.
class DBTable(DeclarativeBase):
    metadata: sqlalchemy.MetaData = sqlalchemy.MetaData()  # type: ignore


# Alias used throughout the codebase -- all ORM models inherit from Base.
Base: typing.Type[DeclarativeBase] = DBTable
