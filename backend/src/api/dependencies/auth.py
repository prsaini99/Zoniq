# Authentication dependencies -- FastAPI dependency-injection functions for extracting
# and validating the current user from JWT bearer tokens
import fastapi
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession

from src.api.dependencies.session import get_async_session
from src.config.manager import settings
from src.models.db.account import Account, UserRole
from src.repository.crud.account import AccountCRUDRepository
from src.securities.authorizations.jwt import jwt_generator

# Shared HTTP Bearer scheme used by endpoints that require authentication
security = HTTPBearer()


# Dependency: extracts and validates the JWT token, then loads the corresponding Account
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    async_session: SQLAlchemyAsyncSession = Depends(get_async_session),
) -> Account:
    """
    Dependency to get the current authenticated user from JWT token.
    """
    token = credentials.credentials

    # Decode the JWT to extract the username and email claims
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

    # Look up the account in the database by the username embedded in the token
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

    # Prevent blocked accounts from accessing protected resources
    if account.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked",
        )

    return account


# Dependency: chains on get_current_user and additionally verifies the user has admin role
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


# Dependency: like get_current_user but returns None instead of raising when no token is present.
# Useful for endpoints that behave differently for authenticated vs anonymous users.
async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    async_session: SQLAlchemyAsyncSession = Depends(get_async_session),
) -> Account | None:
    """
    Dependency to optionally get the current user.
    Returns None if no valid token is provided.
    """
    # No credentials supplied -- treat as anonymous request
    if credentials is None:
        return None

    token = credentials.credentials

    # Silently return None on invalid/expired tokens instead of raising
    try:
        username, email = jwt_generator.retrieve_details_from_token(
            token=token, secret_key=settings.JWT_SECRET_KEY
        )
    except ValueError:
        return None

    account_repo = AccountCRUDRepository(async_session=async_session)

    # Return the account only if it exists and is not blocked
    try:
        account = await account_repo.read_account_by_username(username=username)
        if account and not account.is_blocked:
            return account
    except Exception:
        pass

    return None
