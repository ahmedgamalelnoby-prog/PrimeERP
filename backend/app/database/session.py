from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Import the central registry whenever a database session is created.
# This guarantees that all ORM relationships are registered before any
# query can trigger mapper configuration, even when SessionLocal is used
# directly by scripts, tests, or background jobs.
import app.database.models as _database_models  # noqa: F401,E402


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
