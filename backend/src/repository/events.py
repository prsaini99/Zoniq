# Database lifecycle event handlers -- manages connection setup, table creation,
# initial data seeding, and graceful shutdown for the FastAPI application.

from contextlib import asynccontextmanager

import fastapi
import loguru
from sqlalchemy import event
from sqlalchemy.dialects.postgresql.asyncpg import AsyncAdapt_asyncpg_connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, AsyncSessionTransaction
from sqlalchemy.pool.base import _ConnectionRecord

from src.repository.database import async_db
from src.repository.table import Base


# Async context manager that creates a scoped database session from the factory.
# Ensures the session is always closed after use, even on exceptions.
@asynccontextmanager
async def async_db_session():
    """Context manager for creating async database sessions."""
    session: AsyncSession = async_db.async_session_factory()
    try:
        yield session
    finally:
        await session.close()


# SQLAlchemy event listener that fires when a new raw DB-API connection is established.
# Logs connection details for debugging and monitoring pool behavior.
@event.listens_for(target=async_db.async_engine.sync_engine, identifier="connect")
def inspect_db_server_on_connection(
    db_api_connection: AsyncAdapt_asyncpg_connection, connection_record: _ConnectionRecord
) -> None:
    loguru.logger.info(f"New DB API Connection ---\n {db_api_connection}")
    loguru.logger.info(f"Connection Record ---\n {connection_record}")


# SQLAlchemy event listener that fires when a DB-API connection is closed.
# Logs closure details for auditing connection lifecycle.
@event.listens_for(target=async_db.async_engine.sync_engine, identifier="close")
def inspect_db_server_on_close(
    db_api_connection: AsyncAdapt_asyncpg_connection, connection_record: _ConnectionRecord
) -> None:
    loguru.logger.info(f"Closing DB API Connection ---\n {db_api_connection}")
    loguru.logger.info(f"Closed Connection Record ---\n {connection_record}")


# Creates all database tables defined in the Base metadata if they do not already exist.
# Does NOT drop existing tables -- use Alembic migrations for schema changes.
async def initialize_db_tables(connection: AsyncConnection) -> None:
    loguru.logger.info("Database Table Creation --- Initializing . . .")

    # Only create tables that don't exist (don't drop existing tables)
    # Use Alembic migrations for schema changes
    await connection.run_sync(Base.metadata.create_all)

    loguru.logger.info("Database Table Creation --- Successfully Initialized!")


# Seeds essential initial data (e.g., default admin user) after tables are created.
# Catches and logs errors so a seeding failure does not crash the app startup.
async def seed_initial_data() -> None:
    """Seed initial data after tables are created"""
    # Lazy import to avoid circular dependency at module load time.
    from src.seeders.seed_admin import seed_admin_on_startup

    loguru.logger.info("Seeding Initial Data --- Starting . . .")

    try:
        async with async_db.async_session as session:
            await seed_admin_on_startup(async_session=session)
        loguru.logger.info("Seeding Initial Data --- Completed!")
    except Exception as e:
        loguru.logger.error(f"Seeding Initial Data --- Failed: {e}")


# Application startup hook: stores the database instance on app state,
# initializes tables within a transactional connection, and seeds initial data.
async def initialize_db_connection(backend_app: fastapi.FastAPI) -> None:
    loguru.logger.info("Database Connection --- Establishing . . .")

    # Attach the database object to app state so it is accessible throughout the app.
    backend_app.state.db = async_db

    # Begin a transactional connection to create any missing tables.
    async with backend_app.state.db.async_engine.begin() as connection:
        await initialize_db_tables(connection=connection)

    # Seed initial data (admin user)
    await seed_initial_data()

    loguru.logger.info("Database Connection --- Successfully Established!")


# Application shutdown hook: disposes the async engine, releasing all pooled connections.
async def dispose_db_connection(backend_app: fastapi.FastAPI) -> None:
    loguru.logger.info("Database Connection --- Disposing . . .")

    await backend_app.state.db.async_engine.dispose()

    loguru.logger.info("Database Connection --- Successfully Disposed!")
