import os

from app.core.config import Settings


os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///./unsafe.db")
os.environ.setdefault("SECRET_KEY", "your-secret-key-change-this-in-production")
os.environ.setdefault("CORS_ORIGINS", "https://erp.example.com")

try:
    Settings()
except ValueError as exc:
    print(f"Expected production configuration rejection: {exc}")
else:
    raise SystemExit("Production safety validation failed to reject unsafe configuration")
