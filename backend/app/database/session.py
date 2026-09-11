from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# Keep the database session module dependency-free from the ORM model registry.
# Importing all models here creates a circular dependency when any model (or
# service imported by a model) needs SessionLocal during application startup.
# Model registration is owned by the application/Alembic bootstrap instead.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
