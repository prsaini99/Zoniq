# Production-specific settings -- debug is off (inherited default) for security and performance
from src.config.settings.base import BackendBaseSettings
from src.config.settings.environment import Environment


class BackendProdSettings(BackendBaseSettings):
    DESCRIPTION: str | None = "Production Environment."
    ENVIRONMENT: Environment = Environment.PRODUCTION
