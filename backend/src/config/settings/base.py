# Base settings class -- defines all shared configuration values for the backend.
# Environment-specific subclasses (dev, staging, prod) override selected fields.
import logging
import pathlib

import decouple
import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the project root directory (four levels up from this file) to locate the .env file
ROOT_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent.parent.parent.parent.resolve()


class BackendBaseSettings(BaseSettings):
    # --- General application metadata ---
    TITLE: str = "DAPSQL FARN-Stack Template Application"
    VERSION: str = "0.1.0"
    TIMEZONE: str = "UTC"
    DESCRIPTION: str | None = None
    DEBUG: bool = False

    # --- Server configuration (loaded from environment variables) ---
    SERVER_HOST: str = decouple.config("BACKEND_SERVER_HOST", cast=str)  # type: ignore
    SERVER_PORT: int = decouple.config("BACKEND_SERVER_PORT", cast=int)  # type: ignore
    SERVER_WORKERS: int = decouple.config("BACKEND_SERVER_WORKERS", cast=int)  # type: ignore
    API_PREFIX: str = "/api"
    DOCS_URL: str = "/docs"
    OPENAPI_URL: str = "/openapi.json"
    REDOC_URL: str = "/redoc"
    OPENAPI_PREFIX: str = ""

    # --- PostgreSQL database connection settings ---
    DB_POSTGRES_HOST: str = decouple.config("POSTGRES_HOST", cast=str)  # type: ignore
    DB_MAX_POOL_CON: int = decouple.config("DB_MAX_POOL_CON", cast=int)  # type: ignore
    DB_POSTGRES_NAME: str = decouple.config("POSTGRES_DB", cast=str)  # type: ignore
    DB_POSTGRES_PASSWORD: str = decouple.config("POSTGRES_PASSWORD", cast=str)  # type: ignore
    DB_POOL_SIZE: int = decouple.config("DB_POOL_SIZE", cast=int)  # type: ignore
    DB_POOL_OVERFLOW: int = decouple.config("DB_POOL_OVERFLOW", cast=int)  # type: ignore
    DB_POSTGRES_PORT: int = decouple.config("POSTGRES_PORT", cast=int)  # type: ignore
    DB_POSTGRES_SCHEMA: str = decouple.config("POSTGRES_SCHEMA", cast=str)  # type: ignore
    DB_TIMEOUT: int = decouple.config("DB_TIMEOUT", cast=int)  # type: ignore
    DB_POSTGRES_USERNAME: str = decouple.config("POSTGRES_USERNAME", cast=str)  # type: ignore

    # --- Database behaviour flags ---
    IS_DB_ECHO_LOG: bool = decouple.config("IS_DB_ECHO_LOG", cast=bool)  # type: ignore
    IS_DB_FORCE_ROLLBACK: bool = decouple.config("IS_DB_FORCE_ROLLBACK", cast=bool)  # type: ignore
    IS_DB_EXPIRE_ON_COMMIT: bool = decouple.config("IS_DB_EXPIRE_ON_COMMIT", cast=bool)  # type: ignore

    # --- Authentication and JWT token settings ---
    API_TOKEN: str = decouple.config("API_TOKEN", cast=str)  # type: ignore
    AUTH_TOKEN: str = decouple.config("AUTH_TOKEN", cast=str)  # type: ignore
    JWT_TOKEN_PREFIX: str = decouple.config("JWT_TOKEN_PREFIX", cast=str)  # type: ignore
    JWT_SECRET_KEY: str = decouple.config("JWT_SECRET_KEY", cast=str)  # type: ignore
    JWT_SUBJECT: str = decouple.config("JWT_SUBJECT", cast=str)  # type: ignore
    JWT_MIN: int = decouple.config("JWT_MIN", cast=int)  # type: ignore
    JWT_HOUR: int = decouple.config("JWT_HOUR", cast=int)  # type: ignore
    JWT_DAY: int = decouple.config("JWT_DAY", cast=int)  # type: ignore
    # Total JWT expiration time computed as the product of minutes, hours, and days
    JWT_ACCESS_TOKEN_EXPIRATION_TIME: int = JWT_MIN * JWT_HOUR * JWT_DAY

    # --- CORS (Cross-Origin Resource Sharing) settings ---
    IS_ALLOWED_CREDENTIALS: bool = decouple.config("IS_ALLOWED_CREDENTIALS", cast=bool)  # type: ignore
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",  # React default port
        "http://0.0.0.0:3000",
        "http://127.0.0.1:3000",  # React docker port
        "http://127.0.0.1:3001",
        "http://localhost:5173",  # Qwik default port
        "http://0.0.0.0:5173",
        "http://127.0.0.1:5173",  # Qwik docker port
        "http://127.0.0.1:5174",
    ]
    ALLOWED_METHODS: list[str] = ["*"]
    ALLOWED_HEADERS: list[str] = ["*"]

    # --- Logging configuration ---
    LOGGING_LEVEL: int = logging.INFO
    LOGGERS: tuple[str, str] = ("uvicorn.asgi", "uvicorn.access")

    # --- Password hashing and JWT algorithm settings ---
    HASHING_ALGORITHM_LAYER_1: str = decouple.config("HASHING_ALGORITHM_LAYER_1", cast=str)  # type: ignore
    HASHING_ALGORITHM_LAYER_2: str = decouple.config("HASHING_ALGORITHM_LAYER_2", cast=str)  # type: ignore
    HASHING_SALT: str = decouple.config("HASHING_SALT", cast=str)  # type: ignore
    JWT_ALGORITHM: str = decouple.config("JWT_ALGORITHM", cast=str)  # type: ignore

    # --- Admin Configuration ---
    ADMIN_EMAIL: str = decouple.config("ADMIN_EMAIL", default="admin@zoniq.com", cast=str)  # type: ignore
    ADMIN_PASSWORD: str = decouple.config("ADMIN_PASSWORD", default="admin123!", cast=str)  # type: ignore
    ADMIN_USERNAME: str = decouple.config("ADMIN_USERNAME", default="admin", cast=str)  # type: ignore

    # --- OTP (One-Time Password) Configuration ---
    OTP_EXPIRY_MINUTES: int = decouple.config("OTP_EXPIRY_MINUTES", default=10, cast=int)  # type: ignore
    OTP_LENGTH: int = decouple.config("OTP_LENGTH", default=6, cast=int)  # type: ignore

    # --- MSG91 SMS gateway Configuration ---
    MSG91_AUTH_KEY: str = decouple.config("MSG91_AUTH_KEY", default="", cast=str)  # type: ignore
    MSG91_OTP_TEMPLATE_ID: str = decouple.config("MSG91_OTP_TEMPLATE_ID", default="", cast=str)  # type: ignore

    # --- Razorpay payment gateway Configuration ---
    RAZORPAY_KEY_ID: str = decouple.config("RAZORPAY_KEY_ID", default="", cast=str)  # type: ignore
    RAZORPAY_KEY_SECRET: str = decouple.config("RAZORPAY_KEY_SECRET", default="", cast=str)  # type: ignore
    RAZORPAY_WEBHOOK_SECRET: str = decouple.config("RAZORPAY_WEBHOOK_SECRET", default="", cast=str)  # type: ignore

    # --- Email/SMTP Configuration ---
    SMTP_HOST: str = decouple.config("SMTP_HOST", default="smtp.gmail.com", cast=str)  # type: ignore
    SMTP_PORT: int = decouple.config("SMTP_PORT", default=587, cast=int)  # type: ignore
    SMTP_USERNAME: str = decouple.config("SMTP_USERNAME", default="", cast=str)  # type: ignore
    SMTP_PASSWORD: str = decouple.config("SMTP_PASSWORD", default="", cast=str)  # type: ignore
    SMTP_USE_TLS: bool = decouple.config("SMTP_USE_TLS", default=True, cast=bool)  # type: ignore
    FROM_EMAIL: str = decouple.config("FROM_EMAIL", default="noreply@zoniq.com", cast=str)  # type: ignore
    FROM_NAME: str = decouple.config("FROM_NAME", default="ZONIQ", cast=str)  # type: ignore

    # --- Frontend URL used for constructing links in outbound emails ---
    FRONTEND_URL: str = decouple.config("FRONTEND_URL", default="http://localhost:3000", cast=str)  # type: ignore

    # Pydantic settings model configuration: reads from .env, enforces case-sensitive keys
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=f"{str(ROOT_DIR)}/.env",
        validate_assignment=True,
        extra="ignore",
    )

    @property
    def set_backend_app_attributes(self) -> dict[str, str | bool | None]:
        """
        Set all `FastAPI` class' attributes with the custom values defined in `BackendBaseSettings`.
        """
        # Return a dict that can be unpacked as keyword arguments to fastapi.FastAPI(...)
        return {
            "title": self.TITLE,
            "version": self.VERSION,
            "debug": self.DEBUG,
            "description": self.DESCRIPTION,
            "docs_url": self.DOCS_URL,
            "openapi_url": self.OPENAPI_URL,
            "redoc_url": self.REDOC_URL,
            "openapi_prefix": self.OPENAPI_PREFIX,
            "api_prefix": self.API_PREFIX,
        }
