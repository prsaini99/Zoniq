import datetime
from uuid import UUID
from typing import Optional

from loguru import logger

from src.models.db.queue_entry import QueueStatus
from src.repository.crud.queue import QueueCRUDRepository
from src.repository.crud.event import EventCRUDRepository


# Service class for managing event booking queues — handles joining, positioning, and processing
class QueueService:
    """Service for managing event queues"""

    # Average checkout time in minutes, used to estimate wait duration for queued users
    AVG_CHECKOUT_TIME_MINUTES = 3

    # Estimate how many minutes a user at a given position will need to wait
    def estimate_wait_time(
        self,
        position: int,
        batch_size: int,
        processing_minutes: int
    ) -> int:
        """Estimate wait time in minutes based on position"""
        # If the user is within the first batch, they can proceed immediately
        if position <= batch_size:
            return 0

        # Calculate how many complete batches are ahead of this position
        batches_ahead = (position - 1) // batch_size

        # Use the smaller of average checkout time and configured processing time per batch
        estimated_batch_time = min(self.AVG_CHECKOUT_TIME_MINUTES, processing_minutes)

        return batches_ahead * estimated_batch_time

    # Add a user to the event queue after validating queue availability and booking status
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

        # Reject if the event does not use queue-based booking
        if not event.queue_enabled:
            raise ValueError("Queue is not enabled for this event")

        # Reject if booking window is not currently open
        if not event.is_booking_open:
            raise ValueError("Booking is not currently open for this event")

        # Create the queue entry in the database
        entry = await queue_repo.join_queue(
            event_id=event_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Retrieve the user's position and how many users are ahead
        _, ahead_count = await queue_repo.get_user_position(
            event_id=event_id,
            user_id=user_id
        )

        # Calculate estimated wait time based on position and event batch settings
        estimated_wait = self.estimate_wait_time(
            position=entry.position,
            batch_size=event.queue_batch_size,
            processing_minutes=event.queue_processing_minutes,
        )

        # Return queue entry details to the caller
        return {
            "queue_entry_id": entry.id,
            "event_id": event_id,
            "position": entry.position,
            "status": entry.status,
            "estimated_wait_minutes": estimated_wait,
            "total_ahead": ahead_count,
            "joined_at": entry.joined_at,
        }

    # Retrieve the current queue position and status for a specific user
    async def get_position(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
        user_id: int,
    ) -> dict | None:
        """Get user's current position in queue"""
        # Look up the user's queue entry and count of users ahead
        entry, ahead_count = await queue_repo.get_user_position(
            event_id=event_id,
            user_id=user_id
        )

        # Return None if the user is not in the queue
        if not entry:
            return None

        # Fetch event details for batch size and processing time
        event = await event_repo.read_event_by_id(event_id=event_id)

        estimated_wait = self.estimate_wait_time(
            position=entry.position,
            batch_size=event.queue_batch_size,
            processing_minutes=event.queue_processing_minutes,
        )

        # Return position info including whether the user can proceed to booking
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

    # Advance the queue by moving waiting users into the processing state
    async def process_queue(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
    ) -> list[UUID]:
        """Process queue - move waiting users to processing"""
        event = await event_repo.read_event_by_id(event_id=event_id)

        # Skip processing if queue is not enabled for this event
        if not event.queue_enabled:
            return []

        # Expire entries that have exceeded their processing time window
        expired_count = await queue_repo.expire_stale_entries()
        if expired_count > 0:
            logger.info(f"Expired {expired_count} stale queue entries for event {event_id}")

        # Count how many users are currently in the processing state
        current_processing = await queue_repo.count_active_processing(event_id=event_id)

        # Determine how many new users can be moved into processing
        available_slots = event.queue_batch_size - current_processing

        # No available slots — all processing slots are occupied
        if available_slots <= 0:
            return []

        # Fetch the next batch of waiting entries eligible for processing
        entries = await queue_repo.get_entries_to_process(
            event_id=event_id,
            batch_size=available_slots
        )

        # Mark each entry as processing and set their expiry time
        processed_ids = []
        for entry in entries:
            await queue_repo.mark_as_processing(
                entry_id=entry.id,
                processing_minutes=event.queue_processing_minutes
            )
            processed_ids.append(entry.id)
            logger.info(f"Moved user {entry.user_id} to processing for event {event_id}")

        return processed_ids

    # Get a summary of the queue status for a given event (public-facing)
    async def get_queue_status(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
    ) -> dict:
        """Get public queue status for an event"""
        event = await event_repo.read_event_by_id(event_id=event_id)

        # Return a default response if queue is not enabled
        if not event.queue_enabled:
            return {
                "event_id": event_id,
                "queue_enabled": False,
                "total_in_queue": 0,
                "currently_processing": 0,
                "estimated_wait_minutes": None,
                "is_queue_active": False,
            }

        # Retrieve aggregate queue statistics (total waiting, processing, etc.)
        stats = await queue_repo.get_queue_stats(event_id=event_id)

        # Estimate wait time for a hypothetical new joiner (next position in line)
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


# Singleton instance — shared across the application for queue management
queue_service = QueueService()
