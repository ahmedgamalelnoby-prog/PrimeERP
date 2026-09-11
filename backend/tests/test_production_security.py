import os

import pytest

from app.core.config import get_settings
from app.core.security.production import ProductionConfigurationError, validate_production_configuration


def _settings(**overrides):
    values = {
        "DEBUG": False,
        "SECRET_KEY": "x" * 64,
        "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/primeerp",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "REFRESH_TOKEN_EXPIRE_DAYS": 7,
        "CORS_ORIGINS": "https://erp.example.com",
    }
    values.update(overrides)
    return type("SettingsStub", (), values)()


def test_production_configuration_accepts_secure_values(monkeypatch):
    settings = _settings()
    monkeypatch.setattr("app.core.security.production.settings", settings)
    validate_production_configuration()


@pytest.mark.parametrize(
    "overrides",
    [
        {"DEBUG": True},
        {"SECRET_KEY": "short"},
        {"SECRET_KEY": "your-secret-key-change-this-in-production"},
        {"DATABASE_URL": "sqlite:///./primeerp.db"},
        {"ACCESS_TOKEN_EXPIRE_MINUTES": 61},
        {"REFRESH_TOKEN_EXPIRE_DAYS": 32},
        {"CORS_ORIGINS": "*"},
    ],
)
def test_production_configuration_rejects_unsafe_values(monkeypatch, overrides):
    monkeypatch.setattr("app.core.security.production.settings", _settings(**overrides))
    with pytest.raises(ProductionConfigurationError):
        validate_production_configuration()
