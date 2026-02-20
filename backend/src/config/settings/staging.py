# Staging-specific settings -- mirrors production but keeps debug enabled for testing
from src.config.settings.base import BackendBaseSettings
from src.config.settings.environment import Environment


class BackendStageSettings(BackendBaseSettings):
    DESCRIPTION: str | None = "Test Environment."
    DEBUG: bool = True
    ENVIRONMENT: Environment = Environment.STAGING
