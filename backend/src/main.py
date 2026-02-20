# Application entry point -- creates and configures the FastAPI backend server
import fastapi
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from src.api.endpoints import router as api_endpoint_router
from src.config.events import execute_backend_server_event_handler, terminate_backend_server_event_handler
from src.config.manager import settings


def initialize_backend_application() -> fastapi.FastAPI:
    # Create the FastAPI app instance with settings-driven attributes (title, version, debug, docs URLs, etc.)
    app = fastapi.FastAPI(**settings.set_backend_app_attributes)  # type: ignore

    # Configure CORS middleware to control which origins, methods, and headers are permitted
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=settings.IS_ALLOWED_CREDENTIALS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # Register the startup handler (initializes DB connection, starts background workers)
    app.add_event_handler(
        "startup",
        execute_backend_server_event_handler(backend_app=app),
    )
    # Register the shutdown handler (stops background workers, disposes DB connection)
    app.add_event_handler(
        "shutdown",
        terminate_backend_server_event_handler(backend_app=app),
    )

    # Mount all API routes under the configured prefix (e.g. "/api")
    app.include_router(router=api_endpoint_router, prefix=settings.API_PREFIX)

    return app


# Instantiate the application at module level so uvicorn can discover it
backend_app: fastapi.FastAPI = initialize_backend_application()

# Run the server directly when this module is executed as a script
if __name__ == "__main__":
    uvicorn.run(
        app="main:backend_app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        workers=settings.SERVER_WORKERS,
        log_level=settings.LOGGING_LEVEL,
    )
