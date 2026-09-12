from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["development", "test", "staging", "production"]


class Settings(BaseSettings):
    """PrimeERP application settings with explicit production safety checks."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "PrimeERP"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: Environment = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./primeerp_new.db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:3004,"
        "http://127.0.0.1:3004"
    )

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> "Settings":
        """Fail fast when unsafe development defaults are used in production."""
        if self.APP_ENV == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if self.DATABASE_URL.lower().startswith("sqlite"):
                raise ValueError("SQLite is not supported in production; configure PostgreSQL")
            if len(self.SECRET_KEY) < 32 or self.SECRET_KEY == "your-secret-key-change-this-in-production":
                raise ValueError("SECRET_KEY must be a strong random value of at least 32 characters")
            if not self.BACKEND_CORS_ORIGINS:
                raise ValueError("CORS_ORIGINS must contain at least one explicit origin in production")
            if any(origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1") for origin in self.BACKEND_CORS_ORIGINS):
                raise ValueError("Localhost CORS origins are not allowed in production")
        return self

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """Convert comma-separated CORS origins into a clean list."""
        return [
            origin.strip().rstrip("/")
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
