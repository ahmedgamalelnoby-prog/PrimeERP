import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

# Import the settings class under a known-safe baseline first. The config
# module creates its global settings instance at import time, so importing it
# while intentionally unsafe production values are present would fail before
# the actual assertion below can run.
os.environ["APP_ENV"] = "development"
os.environ["DEBUG"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./release_gate_safe.db"
os.environ["SECRET_KEY"] = "release-gate-safe-secret-key-0123456789"
os.environ["CORS_ORIGINS"] = "http://127.0.0.1:3000"

from app.core.config import Settings

# Explicitly override any developer .env values so this gate always tests the
# production safety rules against a known unsafe configuration.
os.environ["APP_ENV"] = "production"
os.environ["DEBUG"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./unsafe.db"
os.environ["SECRET_KEY"] = "your-secret-key-change-this-in-production"
os.environ["CORS_ORIGINS"] = "https://erp.example.com"

try:
    Settings()
except ValueError as exc:
    print(f"Expected production configuration rejection: {exc}")
else:
    raise SystemExit("Production safety validation failed to reject unsafe configuration")
