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
    logs, total = await log_repo.get_logs(
        page=page,
        page_size=page_size,
        admin_id=admin_id,
        action=action,
        entity_type=entity_type,
        start_date=start_date,
        end_date=end_date,
    )

    # Fetch admin usernames
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
    if not log:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Activity log not found",
        )

    # Fetch admin username
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
