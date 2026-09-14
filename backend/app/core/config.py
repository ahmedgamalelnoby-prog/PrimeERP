from __future__ import annotations

from functools import lru_cache
from typing import List, Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]


class Settings(BaseSettings):
    """PrimeERP application settings with explicit production safety checks."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

    APP_NAME: str = "PrimeERP"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: Environment = "development"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./primeerp_new.db"
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:3004,http://127.0.0.1:3004"

    ETA_ENABLED: bool = False
    ETA_IDENTITY_URL: str = "https://id.eta.gov.eg/connect/token"
    ETA_API_BASE_URL: str = "https://api.invoicing.eta.gov.eg"
    ETA_API_VERSION: str = "1"
    ETA_CLIENT_ID: str = ""
    ETA_CLIENT_SECRET: str = ""
    ETA_CLIENT_CERTIFICATE_PATH: str = ""
    ETA_CLIENT_CERTIFICATE_PASSWORD: str = ""
    ETA_NOTIFICATION_SECRET: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-5.6-luna"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_STARTTLS: bool = True

    WHATSAPP_ENABLED: bool = False
    WHATSAPP_API_BASE_URL: str = "https://graph.facebook.com/v23.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> "Settings":
        if "+psycopg2" in self.DATABASE_URL:
            self.DATABASE_URL = self.DATABASE_URL.replace("+psycopg2", "+psycopg")
        if self.APP_ENV == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if self.DATABASE_URL.lower().startswith("sqlite"):
                raise ValueError("SQLite is not supported in production; configure PostgreSQL")
            if len(self.SECRET_KEY) < 32 or self.SECRET_KEY == "your-secret-key-change-this-in-production":
                raise ValueError("SECRET_KEY must be a strong random value of at least 32 characters")
            origins = self.BACKEND_CORS_ORIGINS
            if not origins:
                raise ValueError("CORS_ORIGINS must contain at least one explicit origin in production")
            if any(origin.startswith(("http://localhost", "http://127.0.0.1")) for origin in origins):
                raise ValueError("Localhost CORS origins are not allowed in production")
            if any(not origin.startswith("https://") for origin in origins):
                raise ValueError("Production CORS origins must use HTTPS")
            if self.ETA_ENABLED and (not self.ETA_CLIENT_ID or not self.ETA_CLIENT_SECRET):
                raise ValueError("ETA_CLIENT_ID and ETA_CLIENT_SECRET are required when ETA integration is enabled")
            if self.ETA_ENABLED and not self.ETA_API_BASE_URL.startswith("https://"):
                raise ValueError("ETA_API_BASE_URL must use HTTPS")
            if self.ETA_ENABLED and not self.ETA_NOTIFICATION_SECRET:
                raise ValueError("ETA_NOTIFICATION_SECRET is required when ETA integration is enabled")
            if self.WHATSAPP_ENABLED and (not self.WHATSAPP_PHONE_NUMBER_ID or not self.WHATSAPP_ACCESS_TOKEN):
                raise ValueError("WhatsApp credentials are required when WhatsApp delivery is enabled")
            if self.OPENAI_API_KEY and not self.OPENAI_BASE_URL.startswith("https://"):
                raise ValueError("OPENAI_BASE_URL must use HTTPS in production")
        return self

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
