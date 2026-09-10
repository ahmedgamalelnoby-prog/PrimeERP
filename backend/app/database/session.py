from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Import the central registry only after SessionLocal has been created.
# The model registry imports modules that expose UnitOfWork, which imports
# SessionLocal. Keeping this import after the factory definition prevents a
# circular import during application startup while still ensuring that all
# ORM models are registered before sessions are used.
import app.database.models as _database_models  # noqa: E402,F401


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
