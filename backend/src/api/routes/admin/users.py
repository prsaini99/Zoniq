# Admin user management routes -- provides endpoints for listing, searching,
# and retrieving user accounts. All endpoints require admin authentication.

import fastapi
from fastapi import Depends

from src.api.dependencies.auth import require_admin
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.account import AdminAccountView, AdminUserListResponse
from src.models.schemas.admin import AdminDashboardStats
from src.repository.crud.account import AccountCRUDRepository

router = fastapi.APIRouter(prefix="/users", tags=["admin-users"])


# Helper function to convert an Account ORM model into the AdminAccountView
# response schema, mapping all relevant fields including verification and block status.
def _build_admin_account_view(account: Account) -> AdminAccountView:
    """Helper to build admin account view"""
    return AdminAccountView(
        id=account.id,
        username=account.username,
        email=account.email,
        role=account.role,
        phone=account.phone,
        full_name=account.full_name,
        is_verified=account.is_verified,
        is_active=account.is_active,
        is_phone_verified=account.is_phone_verified,
        is_blocked=account.is_blocked,
        blocked_reason=account.blocked_reason,
        last_login_at=account.last_login_at,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


# GET /admin/users -- Paginated user listing with optional search.
# Accepts page, page_size, and search query params. Returns a paginated
# list of all user accounts along with the total count.
@router.get(
    "",
    name="admin:list-users",
    response_model=AdminUserListResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    admin: Account = Depends(require_admin),
    account_repo: AccountCRUDRepository = Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AdminUserListResponse:
    """List all users with pagination (admin only)"""
    # Fetch paginated accounts from the database, applying optional search filter
    accounts, total = await account_repo.read_accounts_paginated(
        page=page,
        page_size=page_size,
        search=search,
    )

    # Transform each Account ORM object into the admin-facing response schema
    return AdminUserListResponse(
        users=[_build_admin_account_view(account) for account in accounts],
        total=total,
        page=page,
        page_size=page_size,
    )


# GET /admin/users/stats -- Returns aggregate user statistics for the
# admin dashboard (e.g. total users, active users, new registrations).
@router.get(
    "/stats",
    name="admin:user-stats",
    response_model=AdminDashboardStats,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_user_stats(
    admin: Account = Depends(require_admin),
    account_repo: AccountCRUDRepository = Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AdminDashboardStats:
    """Get user statistics for admin dashboard"""
    # Retrieve aggregate stats from the account repository and map to response schema
    stats = await account_repo.get_stats()
    return AdminDashboardStats(**stats)


# GET /admin/users/{user_id} -- Retrieve a single user's full account details
# by their numeric ID. Returns 404 if the user does not exist.
@router.get(
    "/{user_id}",
    name="admin:get-user",
    response_model=AdminAccountView,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_user(
    user_id: int,
    admin: Account = Depends(require_admin),
    account_repo: AccountCRUDRepository = Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AdminAccountView:
    """Get a specific user by ID (admin only)"""
    # Look up the account by primary key
    account = await account_repo.read_account_by_id(id=user_id)
    # Return 404 if no matching account exists
    if not account:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return _build_admin_account_view(account)
