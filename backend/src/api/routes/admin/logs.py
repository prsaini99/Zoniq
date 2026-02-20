# Admin activity log routes -- provides read-only endpoints for viewing
# the admin audit trail. Every admin action (create, update, delete, etc.)
# is recorded as an activity log entry. These endpoints allow admins to
# review the log with filtering and pagination.

import datetime

import fastapi
from fastapi import Depends

from src.api.dependencies.auth import require_admin
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.admin import AdminActivityLogView, AdminActivityLogListResponse
from src.repository.crud.admin_log import AdminLogCRUDRepository
from src.repository.crud.account import AccountCRUDRepository

router = fastapi.APIRouter(prefix="/logs", tags=["admin-logs"])


# GET /admin/logs -- Paginated list of admin activity logs with optional
# filters for admin_id, action type, entity_type, and date range. For
# each log entry, the admin's username is resolved by looking up the
# account record. If the account lookup fails, the username is left as None.
@router.get(
    "",
    name="admin:list-activity-logs",
    response_model=AdminActivityLogListResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_activity_logs(
    page: int = 1,
    page_size: int = 20,
    admin_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    start_date: datetime.datetime | None = None,
    end_date: datetime.datetime | None = None,
    admin: Account = Depends(require_admin),
    log_repo: AdminLogCRUDRepository = Depends(get_repository(repo_type=AdminLogCRUDRepository)),
    account_repo: AccountCRUDRepository = Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AdminActivityLogListResponse:
    """List admin activity logs with pagination and filtering (admin only)"""
    # Fetch paginated logs with the given filters
    logs, total = await log_repo.get_logs(
        page=page,
        page_size=page_size,
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date,
    )

    # Fetch admin usernames -- enrich each log with the admin's username
    # by looking up their account. Errors are silently caught so a deleted
    # or missing admin account does not break the log listing.
    log_views = []
    for log in logs:
        admin_username = None
        if log.admin_id:
            try:
                admin_account = await account_repo.read_account_by_id(id=log.admin_id)
                if admin_account:
                    admin_username = admin_account.username
            except Exception:
                pass

        log_views.append(
            AdminActivityLogView(
                id=log.id,
                admin_id=log.admin_id,
                admin_username=admin_username,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at,
            )
        )

    return AdminActivityLogListResponse(
        logs=log_views,
        total=total,
        page=page,
        page_size=page_size,
    )


# GET /admin/logs/{log_id} -- Retrieve a single activity log entry by its
# ID. Returns 404 if the log entry does not exist. Also resolves the
# admin username for display.
@router.get(
    "/{log_id}",
    name="admin:get-activity-log",
    response_model=AdminActivityLogView,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_activity_log(
    log_id: int,
    admin: Account = Depends(require_admin),
    log_repo: AdminLogCRUDRepository = Depends(get_repository(repo_type=AdminLogCRUDRepository)),
    account_repo: AccountCRUDRepository = Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AdminActivityLogView:
    """Get a specific activity log by ID (admin only)"""
    log = await log_repo.get_log_by_id(log_id=log_id)
    # Return 404 if no log entry matches the given ID
    if not log:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Activity log not found",
        )

    # Fetch admin username -- resolve the admin_id to a username for display
    admin_username = None
    if log.admin_id:
        try:
            admin_account = await account_repo.read_account_by_id(id=log.admin_id)
            if admin_account:
                admin_username = admin_account.username
        except Exception:
            pass

    return AdminActivityLogView(
        id=log.id,
        admin_id=log.admin_id,
        admin_username=admin_username,
        action=log.action,
        entity_type=log.entity_type,
        entity_id=log.entity_id,
        details=log.details,
        ip_address=log.ip_address,
        created_at=log.created_at,
    )
