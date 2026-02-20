import asyncio
from loguru import logger

from src.repository.crud.queue import QueueCRUDRepository
from src.repository.crud.event import EventCRUDRepository
from src.repository.events import async_db_session
from src.services.queue_service import queue_service
from src.services.websocket_manager import queue_connection_manager


# Background worker that periodically processes event queues and sends real-time updates via WebSocket
class QueueProcessor:
    """Background worker to process queue progression."""

    # Initialize with a configurable polling interval (default 5 seconds)
    def __init__(self, interval_seconds: int = 5):
        self.interval_seconds = interval_seconds
        # Reference to the running asyncio task
        self._task: asyncio.Task | None = None
        # Flag to control the processing loop
        self._running = False

    # Start the background queue processing loop as an asyncio task
    async def start(self):
        """Start the queue processor."""
        # Prevent starting multiple instances
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Queue processor started")

    # Gracefully stop the background processing loop and cancel the task
    async def stop(self):
        """Stop the queue processor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Queue processor stopped")

    # Main loop that repeatedly processes all queues at the configured interval
    async def _run(self):
        """Main processing loop."""
        while self._running:
            try:
                await self._process_all_queues()
            except Exception as e:
                # Log errors but keep the loop running
                logger.error(f"Error in queue processor: {e}")

            # Wait for the configured interval before the next processing cycle
            await asyncio.sleep(self.interval_seconds)

    # Iterate over all events with active WebSocket connections and process their queues
    async def _process_all_queues(self):
        """Process all active event queues."""
        # Only process events that have users actively connected via WebSocket
        active_event_ids = queue_connection_manager.get_active_event_ids()

        # Skip if no events have active connections
        if not active_event_ids:
            return

        # Open a database session for queue and event CRUD operations
        async with async_db_session() as session:
            queue_repo = QueueCRUDRepository(async_session=session)
            event_repo = EventCRUDRepository(async_session=session)

            # Process each event's queue independently, catching per-event errors
            for event_id in active_event_ids:
                try:
                    await self._process_event_queue(
                        queue_repo=queue_repo,
                        event_repo=event_repo,
                        event_id=event_id,
                    )
                except Exception as e:
                    logger.error(f"Error processing queue for event {event_id}: {e}")

    # Process a single event's queue: advance entries and send position updates to connected users
    async def _process_event_queue(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
    ):
        """Process a single event's queue."""
        # Move eligible waiting entries to processing status
        processed_ids = await queue_service.process_queue(
            queue_repo=queue_repo,
            event_repo=event_repo,
            event_id=event_id,
        )

        if processed_ids:
            logger.info(f"Processed {len(processed_ids)} entries for event {event_id}")

        # Fetch all active queue entries and event details for position calculations
        entries = await queue_repo.get_all_active_entries_for_event(event_id=event_id)
        event = await event_repo.read_event_by_id(event_id=event_id)

        # Get the set of users currently connected via WebSocket for this event
        connected_users = queue_connection_manager.get_connected_users(event_id)

        # Send position updates only to users who are connected via WebSocket
        for entry in entries:
            if entry.user_id in connected_users:
                # Count how many active entries are ahead of this user in the queue
                ahead_count = sum(
                    1 for e in entries
                    if e.position < entry.position
                    and e.status in ("waiting", "processing")
                )

                # Estimate the wait time based on queue position and event batch settings
                estimated_wait = queue_service.estimate_wait_time(
                    position=entry.position,
                    batch_size=event.queue_batch_size,
                    processing_minutes=event.queue_processing_minutes,
                )

                # Format the expiry timestamp as an ISO string if present
                expires_at_str = None
                if entry.expires_at:
                    expires_at_str = entry.expires_at.isoformat()

                # Determine if the user can proceed to booking (processing and not expired)
                can_proceed = entry.status == "processing" and not entry.is_expired

                # Send the real-time position update via WebSocket
                await queue_connection_manager.send_position_update(
                    event_id=event_id,
                    user_id=entry.user_id,
                    position=entry.position,
                    status=entry.status,
                    estimated_wait=estimated_wait,
                    total_ahead=ahead_count,
                    expires_at=expires_at_str,
                    can_proceed=can_proceed,
                )

        # Send heartbeat to all connected users to keep WebSocket connections alive
        for user_id in connected_users:
            await queue_connection_manager.send_heartbeat(event_id, user_id)


# Singleton instance — started during application boot and runs in the background
queue_processor = QueueProcessor()
