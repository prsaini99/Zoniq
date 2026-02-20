# Database connection module -- configures and initializes the async PostgreSQL engine,
# session factory, and connection pool using SQLAlchemy's asyncpg driver.

from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import (
    async_sessionmaker as sqlalchemy_async_sessionmaker,
    AsyncEngine as SQLAlchemyAsyncEngine,
    AsyncSession as SQLAlchemyAsyncSession,
    create_async_engine as create_sqlalchemy_async_engine,
)
from sqlalchemy.pool import Pool as SQLAlchemyPool, NullPool

from src.config.manager import settings


# Encapsulates async database engine, session factory, and connection pool configuration.
class AsyncDatabase:
    def __init__(self):
        # Build the PostgreSQL connection URI from settings, URL-encoding username and password
        # to handle special characters safely.
        self.postgres_uri: str = f"{settings.DB_POSTGRES_SCHEMA}://{quote_plus(settings.DB_POSTGRES_USERNAME)}:{quote_plus(settings.DB_POSTGRES_PASSWORD)}@{settings.DB_POSTGRES_HOST}:{settings.DB_POSTGRES_PORT}/{settings.DB_POSTGRES_NAME}"
        # Create the async engine with configurable echo logging, pool size, and overflow limits.
        self.async_engine: SQLAlchemyAsyncEngine = create_sqlalchemy_async_engine(
            url=self.set_async_db_uri,
            echo=settings.IS_DB_ECHO_LOG,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_POOL_OVERFLOW,
        )
        # Use session factory instead of single session instance
        # expire_on_commit=False prevents lazy-load issues after commit in async context.
        self.async_session_factory: sqlalchemy_async_sessionmaker[SQLAlchemyAsyncSession] = sqlalchemy_async_sessionmaker(
            bind=self.async_engine,
            class_=SQLAlchemyAsyncSession,
            expire_on_commit=False,
        )
        # Keep for backward compatibility with existing code
        # Single shared session instance -- prefer the factory for new code.
        self.async_session: SQLAlchemyAsyncSession = SQLAlchemyAsyncSession(bind=self.async_engine, expire_on_commit=False)
        # Expose the underlying connection pool for monitoring or introspection.
        self.pool: SQLAlchemyPool = self.async_engine.pool

    @property
    def set_async_db_uri(self) -> str:
        """
        Set the synchronous database driver into asynchronous version by utilizing AsyncPG:

            `postgresql://` => `postgresql+asyncpg://`
        """
        # Replace the default sync driver scheme with the asyncpg async driver scheme.
        return self.postgres_uri.replace("postgresql://", "postgresql+asyncpg://")


# Module-level singleton -- imported throughout the app to access the shared engine and sessions.
async_db: AsyncDatabase = AsyncDatabase()
