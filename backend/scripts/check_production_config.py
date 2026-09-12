import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))

# Explicitly override any developer .env values so this gate always tests the
# production safety rules against a known unsafe configuration.
os.environ["APP_ENV"] = "production"
os.environ["DEBUG"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./unsafe.db"
os.environ["SECRET_KEY"] = "your-secret-key-change-this-in-production"
os.environ["CORS_ORIGINS"] = "https://erp.example.com"

from app.core.config import Settings

try:
    Settings()
except ValueError as exc:
    print(f"Expected production configuration rejection: {exc}")
else:
    raise SystemExit("Production safety validation failed to reject unsafe configuration")
