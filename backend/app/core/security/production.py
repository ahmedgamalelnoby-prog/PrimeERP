from __future__ import annotations

from urllib.parse import urlparse

from app.core.config import settings


class ProductionConfigurationError(RuntimeError):
    """Raised when mandatory production security settings are unsafe."""


def validate_production_configuration() -> None:
    """Fail fast on configurations that must never reach a production server."""
    if settings.DEBUG:
        raise ProductionConfigurationError("DEBUG must be false in production")

    if settings.SECRET_KEY == "your-secret-key-change-this-in-production" or len(settings.SECRET_KEY) < 32:
        raise ProductionConfigurationError("SECRET_KEY must be a strong value of at least 32 characters")

    database_scheme = urlparse(settings.DATABASE_URL).scheme
    if database_scheme.startswith("sqlite"):
        raise ProductionConfigurationError("SQLite is not supported in production; configure PostgreSQL")

    if settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0 or settings.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
        raise ProductionConfigurationError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 60")

    if settings.REFRESH_TOKEN_EXPIRE_DAYS <= 0 or settings.REFRESH_TOKEN_EXPIRE_DAYS > 31:
        raise ProductionConfigurationError("REFRESH_TOKEN_EXPIRE_DAYS must be between 1 and 31")

    if not settings.BACKEND_CORS_ORIGINS or "*" in settings.BACKEND_CORS_ORIGINS:
        raise ProductionConfigurationError("CORS_ORIGINS must contain explicit trusted origins")
