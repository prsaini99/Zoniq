import typing

import fastapi
import loguru

from src.repository.events import dispose_db_connection, initialize_db_connection
from src.workers.queue_processor import queue_processor


def execute_backend_server_event_handler(backend_app: fastapi.FastAPI) -> typing.Any:
    async def launch_backend_server_events() -> None:
        await initialize_db_connection(backend_app=backend_app)
        # Start queue processor
        await queue_processor.start()

    return launch_backend_server_events


def terminate_backend_server_event_handler(backend_app: fastapi.FastAPI) -> typing.Any:
    @loguru.logger.catch
    async def stop_backend_server_events() -> None:
        # Stop queue processor
        await queue_processor.stop()
        await dispose_db_connection(backend_app=backend_app)

    return stop_backend_server_events
