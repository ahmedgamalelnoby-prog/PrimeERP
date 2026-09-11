from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """PrimeERP application settings with explicit production guardrails."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "PrimeERP"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./primeerp_new.db"

    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:5173,"
        "http://127.0.0.1:5173,"
        "http://localhost:3004,"
        "http://127.0.0.1:3004"
    )

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_runtime_security(self) -> "Settings":
        if self.ENVIRONMENT.strip().lower() == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if self.SECRET_KEY == "your-secret-key-change-this-in-production" or len(self.SECRET_KEY) < 32:
                raise ValueError("A unique SECRET_KEY of at least 32 characters is required in production")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("SQLite is not supported in production; configure PostgreSQL")
            if not self.BACKEND_CORS_ORIGINS or "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("Explicit non-wildcard CORS origins are required in production")
            if self.ACCESS_TOKEN_EXPIRE_MINUTES <= 0 or self.REFRESH_TOKEN_EXPIRE_DAYS <= 0:
                raise ValueError("Token expiration settings must be positive")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
