# Queue CRUD repository -- manages a virtual waiting queue for high-demand events.
# Users join a FIFO queue, are moved to PROCESSING state in batches, and can then
# proceed to booking. Handles position tracking, expiry of stale entries, and
# concurrent-safe batch processing using FOR UPDATE SKIP LOCKED.

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

    # Determines the next available position in the queue for a given event.
    # Finds the maximum position among active (WAITING or PROCESSING) entries and adds 1.
    # Returns 1 if the queue is empty.
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

    # Adds a user to the event queue. If the user already has an active entry
    # (WAITING or PROCESSING), returns the existing entry instead of creating a duplicate.
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

        # Create a new WAITING entry at the end of the queue.
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

    # Fetches a queue entry by its UUID primary key.
    # Raises EntityDoesNotExist if the entry is not found.
    async def get_entry_by_id(self, entry_id: UUID) -> QueueEntry:
        """Get a queue entry by ID"""
        stmt = sqlalchemy.select(QueueEntry).where(QueueEntry.id == entry_id)
        result = await self.async_session.execute(statement=stmt)
        entry = result.scalar()

        if not entry:
            raise EntityDoesNotExist(f"Queue entry with id '{entry_id}' does not exist!")

        return entry

    # Looks up a user's active queue entry (WAITING or PROCESSING) for a specific event.
    # Returns None if the user is not currently in the queue.
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

    # Returns the user's queue entry and the number of people ahead of them.
    # "Ahead" means active entries with a lower position number.
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

    # Allows a user to voluntarily leave the queue by marking their entry as LEFT.
    # Returns False if no active entry was found.
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

    # Transitions a queue entry from WAITING to PROCESSING with a time-limited window.
    # The user must complete their booking within processing_minutes or the entry expires.
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

    # Marks a user's queue entry as COMPLETED after they successfully finish booking.
    # Returns False if no active entry was found.
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

    # Expires entries that are in PROCESSING state but have exceeded their allotted time.
    # Intended to be run periodically as a background task.
    # Returns the number of entries that were expired.
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

    # Returns queue statistics for an event: counts of WAITING and PROCESSING entries.
    # Useful for admin dashboards and queue status displays.
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

    # Fetches the next batch of WAITING entries to promote to PROCESSING.
    # Uses FOR UPDATE SKIP LOCKED for safe concurrent access -- multiple workers
    # can call this simultaneously without processing the same entries.
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

    # Counts the number of users currently in PROCESSING state for an event.
    # Used to determine how many more users can be promoted from the waiting queue.
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

    # Returns all active (WAITING and PROCESSING) queue entries for an event,
    # ordered by position. Used for broadcasting real-time queue updates to clients.
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
