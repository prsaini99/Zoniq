import datetime
import typing
from uuid import UUID

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.queue_entry import QueueEntry, QueueStatus
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist


class QueueCRUDRepository(BaseCRUDRepository):
    """CRUD operations for queue entries"""

    async def get_next_position(self, event_id: int) -> int:
        """Get the next available position in queue for an event"""
        stmt = (
            sqlalchemy.select(
                sqlalchemy.func.coalesce(
                    sqlalchemy.func.max(QueueEntry.position), 0
                ) + 1
            )
            .where(QueueEntry.event_id == event_id)
            .where(QueueEntry.status.in_([
                QueueStatus.WAITING.value,
                QueueStatus.PROCESSING.value
            ]))
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalar() or 1

    async def join_queue(
        self,
        event_id: int,
        user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> QueueEntry:
        """Add user to queue for an event"""
        # Check if user already has an active entry
        existing = await self.get_active_entry(event_id=event_id, user_id=user_id)
        if existing:
            return existing

        # Get next position
        position = await self.get_next_position(event_id=event_id)

        new_entry = QueueEntry(
            event_id=event_id,
            user_id=user_id,
            position=position,
            status=QueueStatus.WAITING.value,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.async_session.add(instance=new_entry)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_entry)

        return new_entry

    async def get_entry_by_id(self, entry_id: UUID) -> QueueEntry:
        """Get a queue entry by ID"""
        stmt = sqlalchemy.select(QueueEntry).where(QueueEntry.id == entry_id)
        result = await self.async_session.execute(statement=stmt)
        entry = result.scalar()

        if not entry:
            raise EntityDoesNotExist(f"Queue entry with id '{entry_id}' does not exist!")

        return entry

    async def get_active_entry(self, event_id: int, user_id: int) -> QueueEntry | None:
        """Get user's active queue entry for an event"""
        stmt = (
            sqlalchemy.select(QueueEntry)
            .where(QueueEntry.event_id == event_id)
            .where(QueueEntry.user_id == user_id)
            .where(QueueEntry.status.in_([
                QueueStatus.WAITING.value,
                QueueStatus.PROCESSING.value
            ]))
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalar()

    async def get_user_position(self, event_id: int, user_id: int) -> tuple[QueueEntry | None, int]:
        """Get user's queue entry and count of people ahead"""
        entry = await self.get_active_entry(event_id=event_id, user_id=user_id)

        if not entry:
            return None, 0

        # Count entries ahead (lower position, active status)
        stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(QueueEntry)
            .where(QueueEntry.event_id == event_id)
            .where(QueueEntry.position < entry.position)
            .where(QueueEntry.status.in_([
                QueueStatus.WAITING.value,
                QueueStatus.PROCESSING.value
            ]))
        )
        result = await self.async_session.execute(statement=stmt)
        ahead_count = result.scalar() or 0

        return entry, ahead_count

    async def leave_queue(self, event_id: int, user_id: int) -> bool:
        """Remove user from queue"""
        entry = await self.get_active_entry(event_id=event_id, user_id=user_id)

        if not entry:
            return False

        stmt = (
            sqlalchemy.update(QueueEntry)
            .where(QueueEntry.id == entry.id)
            .values(status=QueueStatus.LEFT.value)
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return True

    async def mark_as_processing(
        self,
        entry_id: UUID,
        processing_minutes: int = 10
    ) -> QueueEntry:
        """Mark entry as processing with expiry time"""
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(minutes=processing_minutes)

        stmt = (
            sqlalchemy.update(QueueEntry)
            .where(QueueEntry.id == entry_id)
            .values(
                status=QueueStatus.PROCESSING.value,
                processed_at=now,
                expires_at=expires_at,
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.get_entry_by_id(entry_id=entry_id)

    async def mark_as_completed(self, event_id: int, user_id: int) -> bool:
        """Mark user's queue entry as completed"""
        entry = await self.get_active_entry(event_id=event_id, user_id=user_id)

        if not entry:
            return False

        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            sqlalchemy.update(QueueEntry)
            .where(QueueEntry.id == entry.id)
            .values(
                status=QueueStatus.COMPLETED.value,
                completed_at=now,
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return True

    async def expire_stale_entries(self) -> int:
        """Expire entries that exceeded their processing time"""
        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            sqlalchemy.update(QueueEntry)
            .where(QueueEntry.status == QueueStatus.PROCESSING.value)
            .where(QueueEntry.expires_at < now)
            .values(status=QueueStatus.EXPIRED.value)
        )
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return result.rowcount or 0

    async def get_queue_stats(self, event_id: int) -> dict:
        """Get queue statistics for an event"""
        waiting_stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(QueueEntry)
            .where(QueueEntry.event_id == event_id)
            .where(QueueEntry.status == QueueStatus.WAITING.value)
        )
        waiting_result = await self.async_session.execute(statement=waiting_stmt)
        waiting_count = waiting_result.scalar() or 0

        processing_stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(QueueEntry)
            .where(QueueEntry.event_id == event_id)
            .where(QueueEntry.status == QueueStatus.PROCESSING.value)
        )
        processing_result = await self.async_session.execute(statement=processing_stmt)
        processing_count = processing_result.scalar() or 0

        return {
            "total_in_queue": waiting_count + processing_count,
            "waiting": waiting_count,
            "processing": processing_count,
        }

    async def get_entries_to_process(
        self,
        event_id: int,
        batch_size: int
    ) -> typing.Sequence[QueueEntry]:
        """Get next batch of entries to move to processing"""
        # Use FOR UPDATE SKIP LOCKED for concurrent safety
        stmt = (
            sqlalchemy.select(QueueEntry)
            .where(QueueEntry.event_id == event_id)
            .where(QueueEntry.status == QueueStatus.WAITING.value)
            .order_by(QueueEntry.position.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalars().all()

    async def count_active_processing(self, event_id: int) -> int:
        """Count users currently in processing state"""
        stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(QueueEntry)
            .where(QueueEntry.event_id == event_id)
            .where(QueueEntry.status == QueueStatus.PROCESSING.value)
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalar() or 0

    async def get_all_active_entries_for_event(
        self,
        event_id: int
    ) -> typing.Sequence[QueueEntry]:
        """Get all active entries for an event (for broadcasting updates)"""
        stmt = (
            sqlalchemy.select(QueueEntry)
            .where(QueueEntry.event_id == event_id)
            .where(QueueEntry.status.in_([
                QueueStatus.WAITING.value,
                QueueStatus.PROCESSING.value
            ]))
            .order_by(QueueEntry.position.asc())
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalars().all()
