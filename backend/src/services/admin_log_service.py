from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession

from src.models.db.admin_activity_log import AdminAction
from src.repository.crud.admin_log import AdminLogCRUDRepository


# Service class for recording admin activities in the audit log
class AdminLogService:
    """
    Service for logging admin activities.
    """

    # Initialize with an async database session and create the underlying CRUD repository
    def __init__(self, async_session: SQLAlchemyAsyncSession):
        self.repo = AdminLogCRUDRepository(async_session=async_session)

    # Record a generic admin action with optional entity reference and metadata
    async def log_action(
        self,
        admin_id: int,
        action: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log an admin action"""
        await self.repo.create_log(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )

    # Record that an admin blocked a specific user, including the optional reason
    async def log_user_blocked(
        self,
        admin_id: int,
        user_id: int,
        reason: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Log when admin blocks a user"""
        await self.log_action(
            admin_id=admin_id,
            action=AdminAction.BLOCK_USER.value,
            entity_type="user",
            entity_id=user_id,
            details={"reason": reason} if reason else None,
            ip_address=ip_address,
        )

    # Record that an admin unblocked a previously blocked user
    async def log_user_unblocked(
        self,
        admin_id: int,
        user_id: int,
        ip_address: str | None = None,
    ) -> None:
        """Log when admin unblocks a user"""
        await self.log_action(
            admin_id=admin_id,
            action=AdminAction.UNBLOCK_USER.value,
            entity_type="user",
            entity_id=user_id,
            ip_address=ip_address,
        )

    # Record that an admin promoted a regular user to admin role
    async def log_make_admin(
        self,
        admin_id: int,
        user_id: int,
        ip_address: str | None = None,
    ) -> None:
        """Log when admin promotes a user to admin"""
        await self.log_action(
            admin_id=admin_id,
            action=AdminAction.MAKE_ADMIN.value,
            entity_type="user",
            entity_id=user_id,
            ip_address=ip_address,
        )

    # Record that an admin demoted another admin back to regular user role
    async def log_remove_admin(
        self,
        admin_id: int,
        user_id: int,
        ip_address: str | None = None,
    ) -> None:
        """Log when admin demotes an admin to user"""
        await self.log_action(
            admin_id=admin_id,
            action=AdminAction.REMOVE_ADMIN.value,
            entity_type="user",
            entity_id=user_id,
            ip_address=ip_address,
        )
