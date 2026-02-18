from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import (
    async_sessionmaker as sqlalchemy_async_sessionmaker,
    AsyncEngine as SQLAlchemyAsyncEngine,
    AsyncSession as SQLAlchemyAsyncSession,
    create_async_engine as create_sqlalchemy_async_engine,
)
from sqlalchemy.pool import Pool as SQLAlchemyPool, NullPool

from src.config.manager import settings


class AsyncDatabase:
    def __init__(self):
        self.postgres_uri: str = f"{settings.DB_POSTGRES_SCHEMA}://{quote_plus(settings.DB_POSTGRES_USERNAME)}:{quote_plus(settings.DB_POSTGRES_PASSWORD)}@{settings.DB_POSTGRES_HOST}:{settings.DB_POSTGRES_PORT}/{settings.DB_POSTGRES_NAME}"
        self.async_engine: SQLAlchemyAsyncEngine = create_sqlalchemy_async_engine(
            url=self.set_async_db_uri,
            echo=settings.IS_DB_ECHO_LOG,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_OVERFLOW,
        )
        # Use session factory instead of single session instance
        self.async_session_factory: sqlalchemy_async_sessionmaker[SQLAlchemyAsyncSession] = sqlalchemy_async_sessionmaker(
            bind=self.async_engine,
            class_=SQLAlchemyAsyncSession,
            expire_on_commit=False,
        )
        # Keep for backward compatibility with existing code
        self.async_session: SQLAlchemyAsyncSession = SQLAlchemyAsyncSession(bind=self.async_engine, expire_on_commit=False)
        self.pool: SQLAlchemyPool = self.async_engine.pool

    @property
    def set_async_db_uri(self) -> str:
        """
        Set the synchronous database driver into asynchronous version by utilizing AsyncPG:

            `postgresql://` => `postgresql+asyncpg://`
        """
        return self.postgres_uri.replace("postgresql://", "postgresql+asyncpg://")


async_db: AsyncDatabase = AsyncDatabase()
