# Admin activity log CRUD repository for recording and querying admin actions
import datetime
import typing

import sqlalchemy

from src.models.db.admin_activity_log import AdminActivityLog
from src.repository.crud.base import BaseCRUDRepository


class AdminLogCRUDRepository(BaseCRUDRepository):
    # Creates a new admin activity log entry recording an action performed by an admin
    # Captures who did what, to which entity, with optional details and IP address
    async def create_log(
        self,
        admin_id: int,
        action: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> AdminActivityLog:
        """Create a new admin activity log entry"""
        new_log = AdminActivityLog(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )

        self.async_session.add(instance=new_log)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_log)

        return new_log

    # Retrieves admin activity logs with pagination and optional filtering
    # Can filter by admin_id, action type, entity type, and date range
    # Returns a tuple of (log entries for the current page, total matching count)
    async def get_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        admin_id: int | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
    ) -> tuple[typing.Sequence[AdminActivityLog], int]:
        """Get admin activity logs with pagination and filtering"""
        # Base query selecting all admin activity logs
        stmt = sqlalchemy.select(AdminActivityLog)

        # Apply optional filters to narrow down results
        if admin_id:
            stmt = stmt.where(AdminActivityLog.admin_id == admin_id)
        if action:
            stmt = stmt.where(AdminActivityLog.action == action)
        if entity_type:
            stmt = stmt.where(AdminActivityLog.entity_type == entity_type)
        if start_date:
            stmt = stmt.where(AdminActivityLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AdminActivityLog.created_at <= end_date)

        # Count total matching records before applying pagination
        count_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(stmt.subquery())
        count_result = await self.async_session.execute(statement=count_stmt)
        total = count_result.scalar() or 0

        # Order by newest first and apply offset/limit pagination
        stmt = stmt.order_by(AdminActivityLog.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        query = await self.async_session.execute(statement=stmt)
        logs = query.scalars().all()

        return logs, total

    # Fetches a single admin activity log entry by its primary key ID
    # Returns None if the log entry does not exist
    async def get_log_by_id(self, log_id: int) -> AdminActivityLog | None:
        """Get a specific admin activity log by ID"""
        stmt = sqlalchemy.select(AdminActivityLog).where(AdminActivityLog.id == log_id)
        query = await self.async_session.execute(statement=stmt)
        return query.scalar()

    # Retrieves all admin activity logs related to a specific entity (e.g., all actions on user #42)
    # Useful for viewing the complete audit trail of actions performed on an entity
    async def get_logs_for_entity(
        self,
        entity_type: str,
        entity_id: int,
    ) -> typing.Sequence[AdminActivityLog]:
        """Get all admin activity logs for a specific entity"""
        stmt = (
            sqlalchemy.select(AdminActivityLog)
            .where(
                AdminActivityLog.entity_type == entity_type,
                AdminActivityLog.entity_id == entity_id,
            )
            .order_by(AdminActivityLog.created_at.desc())
        )

        query = await self.async_session.execute(statement=stmt)
        return query.scalars().all()
