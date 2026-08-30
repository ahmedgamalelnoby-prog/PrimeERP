from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add backend to Python path.
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.database.base import Base

# Import all models so Alembic can load Base.metadata.
from app.database import models  # noqa: F401

# Keep feature models registered when available.
try:
    from app.modules.platform.features.models import Feature  # noqa: F401
except ImportError:
    Feature = None


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata used by Alembic for schema comparison.
target_metadata = Base.metadata


def include_object(object_, name, type_, reflected, compare_to):
    """Exclude legacy database objects that are intentionally no longer modeled.

    The `plans` table is created by the historical 208197108ac1 migration, while
    the current SaaS model uses `subscription_plans`. We keep the legacy table
    intact for existing databases and prevent `alembic check` from generating a
    destructive DROP TABLE / DROP INDEX operation for it.
    """
    if type_ == "table" and reflected and compare_to is None and name == "plans":
        return False

    if type_ == "index" and reflected and object_.table.name == "plans":
        return False

    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
