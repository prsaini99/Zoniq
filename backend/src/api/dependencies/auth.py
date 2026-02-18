import fastapi
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession

from src.api.dependencies.session import get_async_session
from src.config.manager import settings
from src.models.db.account import Account, UserRole
from src.repository.crud.account import AccountCRUDRepository
from src.securities.authorizations.jwt import jwt_generator

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    async_session: SQLAlchemyAsyncSession = Depends(get_async_session),
) -> Account:
    """
    Dependency to get the current authenticated user from JWT token.
    """
    token = credentials.credentials

    try:
        username, email = jwt_generator.retrieve_details_from_token(
            token=token, secret_key=settings.JWT_SECRET_KEY
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    account_repo = AccountCRUDRepository(async_session=async_session)

    try:
        account = await account_repo.read_account_by_username(username=username)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if account.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked",
        )

    return account


async def require_admin(
    current_user: Account = Depends(get_current_user),
) -> Account:
    """
    Dependency to ensure the current user is an admin.
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    async_session: SQLAlchemyAsyncSession = Depends(get_async_session),
) -> Account | None:
    """
    Dependency to optionally get the current user.
    Returns None if no valid token is provided.
    """
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        username, email = jwt_generator.retrieve_details_from_token(
            token=token, secret_key=settings.JWT_SECRET_KEY
        )
    except ValueError:
        return None

    account_repo = AccountCRUDRepository(async_session=async_session)

    try:
        account = await account_repo.read_account_by_username(username=username)
        if account and not account.is_blocked:
            return account
    except Exception:
        pass

    return None
