"""Global pytest bootstrap for PrimeERP ORM tests.

All tests must use the same canonical SQLAlchemy model registry as the
production application. Importing the registry before test collection makes
string-based relationships deterministic and prevents import-order-dependent
mapper failures.
"""

import pytest
from sqlalchemy.orm import configure_mappers

from app.database import models as _database_models  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def configure_orm_registry():
    """Load and validate the complete application ORM registry once."""
    configure_mappers()
