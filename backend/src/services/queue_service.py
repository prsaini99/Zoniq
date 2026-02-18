import datetime
from uuid import UUID
from typing import Optional

from loguru import logger

from src.models.db.queue_entry import QueueStatus
from src.repository.crud.queue import QueueCRUDRepository
from src.repository.crud.event import EventCRUDRepository


class QueueService:
    """Service for managing event queues"""

    # Average checkout time in minutes (for estimation)
    AVG_CHECKOUT_TIME_MINUTES = 3

    def estimate_wait_time(
        self,
        position: int,
        batch_size: int,
        processing_minutes: int
    ) -> int:
        """Estimate wait time in minutes based on position"""
        if position <= batch_size:
            return 0

        # Calculate how many batches ahead
        batches_ahead = (position - 1) // batch_size

        # Estimate: each batch takes avg_checkout_time or processing_minutes (whichever is less)
        estimated_batch_time = min(self.AVG_CHECKOUT_TIME_MINUTES, processing_minutes)

        return batches_ahead * estimated_batch_time

    async def join_queue(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
        user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        """Join the queue for an event"""
        # Verify event exists and has queue enabled
        event = await event_repo.read_event_by_id(event_id=event_id)

        if not event.queue_enabled:
            raise ValueError("Queue is not enabled for this event")

        if not event.is_booking_open:
            raise ValueError("Booking is not currently open for this event")

        # Join queue
        entry = await queue_repo.join_queue(
            event_id=event_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Get position info
        _, ahead_count = await queue_repo.get_user_position(
            event_id=event_id,
            user_id=user_id
        )

        estimated_wait = self.estimate_wait_time(
            position=entry.position,
            batch_size=event.queue_batch_size,
            processing_minutes=event.queue_processing_minutes,
        )

        return {
            "queue_entry_id": entry.id,
            "event_id": event_id,
            "position": entry.position,
            "status": entry.status,
            "estimated_wait_minutes": estimated_wait,
            "total_ahead": ahead_count,
            "joined_at": entry.joined_at,
        }

    async def get_position(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
        user_id: int,
    ) -> dict | None:
        """Get user's current position in queue"""
        entry, ahead_count = await queue_repo.get_user_position(
            event_id=event_id,
            user_id=user_id
        )

        if not entry:
            return None

        event = await event_repo.read_event_by_id(event_id=event_id)

        estimated_wait = self.estimate_wait_time(
            position=entry.position,
            batch_size=event.queue_batch_size,
            processing_minutes=event.queue_processing_minutes,
        )

        return {
            "queue_entry_id": entry.id,
            "event_id": event_id,
            "position": entry.position,
            "status": entry.status,
            "estimated_wait_minutes": estimated_wait,
            "total_ahead": ahead_count,
            "expires_at": entry.expires_at,
            "can_proceed": entry.status == QueueStatus.PROCESSING.value and not entry.is_expired,
        }

    async def process_queue(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
    ) -> list[UUID]:
        """Process queue - move waiting users to processing"""
        event = await event_repo.read_event_by_id(event_id=event_id)

        if not event.queue_enabled:
            return []

        # First, expire stale processing entries
        expired_count = await queue_repo.expire_stale_entries()
        if expired_count > 0:
            logger.info(f"Expired {expired_count} stale queue entries for event {event_id}")

        # Check how many are currently processing
        current_processing = await queue_repo.count_active_processing(event_id=event_id)

        # Calculate how many slots are available
        available_slots = event.queue_batch_size - current_processing

        if available_slots <= 0:
            return []

        # Get next batch of entries to process
        entries = await queue_repo.get_entries_to_process(
            event_id=event_id,
            batch_size=available_slots
        )

        processed_ids = []
        for entry in entries:
            await queue_repo.mark_as_processing(
                entry_id=entry.id,
                processing_minutes=event.queue_processing_minutes
            )
            processed_ids.append(entry.id)
            logger.info(f"Moved user {entry.user_id} to processing for event {event_id}")

        return processed_ids

    async def get_queue_status(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
    ) -> dict:
        """Get public queue status for an event"""
        event = await event_repo.read_event_by_id(event_id=event_id)

        if not event.queue_enabled:
            return {
                "event_id": event_id,
                "queue_enabled": False,
                "total_in_queue": 0,
                "currently_processing": 0,
                "estimated_wait_minutes": None,
                "is_queue_active": False,
            }

        stats = await queue_repo.get_queue_stats(event_id=event_id)

        # Estimate wait time for someone joining now
        estimated_wait = self.estimate_wait_time(
            position=stats["total_in_queue"] + 1,
            batch_size=event.queue_batch_size,
            processing_minutes=event.queue_processing_minutes,
        )

        return {
            "event_id": event_id,
            "queue_enabled": True,
            "total_in_queue": stats["total_in_queue"],
            "currently_processing": stats["processing"],
            "estimated_wait_minutes": estimated_wait,
            "is_queue_active": event.is_booking_open,
        }


# Singleton instance
queue_service = QueueService()
