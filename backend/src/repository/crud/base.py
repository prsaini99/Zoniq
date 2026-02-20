# Base CRUD repository providing the async database session to all child repositories
from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession


# Abstract base class for all CRUD repositories
# Each repository receives an async SQLAlchemy session via dependency injection
class BaseCRUDRepository:
    def __init__(self, async_session: SQLAlchemyAsyncSession):
        # Store the async database session for use in all CRUD operations
        self.async_session = async_session
