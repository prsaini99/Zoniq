# Lifecycle event handlers for the FastAPI application (startup and shutdown hooks)
import typing

import fastapi
import loguru

from src.repository.events import dispose_db_connection, initialize_db_connection
from src.workers.queue_processor import queue_processor


# Returns an async callable that runs on application startup
def execute_backend_server_event_handler(backend_app: fastapi.FastAPI) -> typing.Any:
    async def launch_backend_server_events() -> None:
        # Establish the database connection pool and attach it to the app
        await initialize_db_connection(backend_app=backend_app)
        # Start the background queue processor for async task execution
        await queue_processor.start()

    return launch_backend_server_events


# Returns an async callable that runs on application shutdown
def terminate_backend_server_event_handler(backend_app: fastapi.FastAPI) -> typing.Any:
    # loguru.logger.catch ensures any exceptions during shutdown are logged
    @loguru.logger.catch
    async def stop_backend_server_events() -> None:
        # Gracefully stop the background queue processor
        await queue_processor.stop()
        # Close all database connections and release the connection pool
        await dispose_db_connection(backend_app=backend_app)

    return stop_backend_server_events
