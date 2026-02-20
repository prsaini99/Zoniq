# Settings manager -- uses a factory pattern to return the correct settings class
# based on the ENVIRONMENT variable (DEV, STAGE, or PROD)
from functools import lru_cache

import decouple

from src.config.settings.base import BackendBaseSettings
from src.config.settings.development import BackendDevSettings
from src.config.settings.environment import Environment
from src.config.settings.production import BackendProdSettings
from src.config.settings.staging import BackendStageSettings


# Factory that maps an environment string to the corresponding settings class
class BackendSettingsFactory:
    def __init__(self, environment: str):
        self.environment = environment

    # Callable interface: returns the appropriate settings instance for the environment
    def __call__(self) -> BackendBaseSettings:
        if self.environment == Environment.DEVELOPMENT.value:
            return BackendDevSettings()
        elif self.environment == Environment.STAGING.value:
            return BackendStageSettings()
        # Default to production settings if environment is not DEV or STAGE
        return BackendProdSettings()


# Cache the settings object so it is only constructed once across the application lifetime
@lru_cache()
def get_settings() -> BackendBaseSettings:
    return BackendSettingsFactory(environment=decouple.config("ENVIRONMENT", default="DEV", cast=str))()  # type: ignore


# Module-level singleton used throughout the codebase to access configuration values
settings: BackendBaseSettings = get_settings()
