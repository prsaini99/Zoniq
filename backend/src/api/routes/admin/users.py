import fastapi
from fastapi import Depends

from src.api.dependencies.auth import require_admin
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.account import AdminAccountView, AdminUserListResponse
from src.models.schemas.admin import AdminDashboardStats
from src.repository.crud.account import AccountCRUDRepository

router = fastapi.APIRouter(prefix="/users", tags=["admin-users"])


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
    accounts, total = await account_repo.read_accounts_paginated(
        page=page,
        page_size=page_size,
        search=search,
    )

    return AdminUserListResponse(
        users=[_build_admin_account_view(account) for account in accounts],
        total=total,
        page=page,
        page_size=page_size,
    )


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
    stats = await account_repo.get_stats()
    return AdminDashboardStats(**stats)


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
    account = await account_repo.read_account_by_id(id=user_id)
    if not account:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return _build_admin_account_view(account)
