import asyncio
from loguru import logger

from src.repository.crud.queue import QueueCRUDRepository
from src.repository.crud.event import EventCRUDRepository
from src.repository.events import async_db_session
from src.services.queue_service import queue_service
from src.services.websocket_manager import queue_connection_manager


class QueueProcessor:
    """Background worker to process queue progression."""

    def __init__(self, interval_seconds: int = 5):
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        """Start the queue processor."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Queue processor started")

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

    async def _run(self):
        """Main processing loop."""
        while self._running:
            try:
                await self._process_all_queues()
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")

            await asyncio.sleep(self.interval_seconds)

    async def _process_all_queues(self):
        """Process all active event queues."""
        # Get all event IDs with active WebSocket connections
        active_event_ids = queue_connection_manager.get_active_event_ids()

        if not active_event_ids:
            return

        async with async_db_session() as session:
            queue_repo = QueueCRUDRepository(async_session=session)
            event_repo = EventCRUDRepository(async_session=session)

            for event_id in active_event_ids:
                try:
                    await self._process_event_queue(
                        queue_repo=queue_repo,
                        event_repo=event_repo,
                        event_id=event_id,
                    )
                except Exception as e:
                    logger.error(f"Error processing queue for event {event_id}: {e}")

    async def _process_event_queue(
        self,
        queue_repo: QueueCRUDRepository,
        event_repo: EventCRUDRepository,
        event_id: int,
    ):
        """Process a single event's queue."""
        # Process the queue (moves waiting to processing)
        processed_ids = await queue_service.process_queue(
            queue_repo=queue_repo,
            event_repo=event_repo,
            event_id=event_id,
        )

        if processed_ids:
            logger.info(f"Processed {len(processed_ids)} entries for event {event_id}")

        # Get all active entries and send updates to connected users
        entries = await queue_repo.get_all_active_entries_for_event(event_id=event_id)
        event = await event_repo.read_event_by_id(event_id=event_id)

        connected_users = queue_connection_manager.get_connected_users(event_id)

        for entry in entries:
            if entry.user_id in connected_users:
                # Calculate position info
                ahead_count = sum(
                    1 for e in entries
                    if e.position < entry.position
                    and e.status in ("waiting", "processing")
                )

                estimated_wait = queue_service.estimate_wait_time(
                    position=entry.position,
                    batch_size=event.queue_batch_size,
                    processing_minutes=event.queue_processing_minutes,
                )

                expires_at_str = None
                if entry.expires_at:
                    expires_at_str = entry.expires_at.isoformat()

                can_proceed = entry.status == "processing" and not entry.is_expired

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

        # Send heartbeat to all connected users for this event
        for user_id in connected_users:
            await queue_connection_manager.send_heartbeat(event_id, user_id)


# Singleton instance
queue_processor = QueueProcessor()
