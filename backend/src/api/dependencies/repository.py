# Repository dependency factory -- creates a FastAPI dependency that instantiates
# any CRUD repository subclass with an injected async database session
import typing

import fastapi
from sqlalchemy.ext.asyncio import (
    async_sessionmaker as sqlalchemy_async_sessionmaker,
    AsyncSession as SQLAlchemyAsyncSession,
)

from src.api.dependencies.session import get_async_session
from src.repository.crud.base import BaseCRUDRepository


# Higher-order function: accepts a repository class and returns a FastAPI-compatible
# dependency that creates an instance of that repository with the current DB session.
# Usage in routes: account_repo: AccountCRUDRepository = Depends(get_repository(AccountCRUDRepository))
def get_repository(
    repo_type: typing.Type[BaseCRUDRepository],
) -> typing.Callable[[SQLAlchemyAsyncSession], BaseCRUDRepository]:
    def _get_repo(
        async_session: SQLAlchemyAsyncSession = fastapi.Depends(get_async_session),
    ) -> BaseCRUDRepository:
        return repo_type(async_session=async_session)

    return _get_repo
