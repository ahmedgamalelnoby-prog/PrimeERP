import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_default_secret():
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+psycopg://primeerp:primeerp@localhost:5432/primeerp",
            CORS_ORIGINS="https://erp.example.com",
        )


def test_production_rejects_sqlite():
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="x" * 64,
            DATABASE_URL="sqlite:///./primeerp.db",
            CORS_ORIGINS="https://erp.example.com",
        )


def test_production_accepts_explicit_secure_configuration():
    settings = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="x" * 64,
        DATABASE_URL="postgresql+psycopg://primeerp:primeerp@localhost:5432/primeerp",
        CORS_ORIGINS="https://erp.example.com",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        REFRESH_TOKEN_EXPIRE_DAYS=7,
    )
    assert settings.ENVIRONMENT == "production"
    assert settings.DEBUG is False
    assert settings.BACKEND_CORS_ORIGINS == ["https://erp.example.com"]
