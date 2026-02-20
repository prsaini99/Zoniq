# Enum defining the supported deployment environments used by the settings factory
import enum


class Environment(str, enum.Enum):
    PRODUCTION: str = "PROD"  # type: ignore
    DEVELOPMENT: str = "DEV"  # type: ignore
    STAGING: str = "STAGE"  # type:ignore
