import contextlib
import typing

import fastapi
from sqlalchemy.ext.asyncio import (
    async_sessionmaker as sqlalchemy_async_sessionmaker,
    AsyncSession as SQLAlchemyAsyncSession,
    AsyncSessionTransaction as SQLAlchemyAsyncSessionTransaction,
)

from src.repository.database import async_db


async def get_async_session() -> typing.AsyncGenerator[SQLAlchemyAsyncSession, None]:
    async with async_db.async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            print(e)
            await session.rollback()
            raise
