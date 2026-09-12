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

# These tables were introduced by an older shipping settlement migration but
# are no longer represented by the canonical ORM model set. They remain in the
# database for upgrade compatibility and must never be proposed for deletion.
_LEGACY_UNMODELED_TABLES = {
    "plans",
    "shipping_settlement_batches",
    "shipping_shipment_settlements",
}


def include_object(object_, name, type_, reflected, compare_to):
    """Limit autogenerate to schema shape owned by the current ORM contract.

    Historical migrations contain several equivalent representations of the
    same business rule (unique constraints vs unique indexes and renamed
    indexes). Treat those physical-index/constraint differences as migration
    implementation details. Column/table presence remains fully checked.
    """
    if type_ == "table" and name in _LEGACY_UNMODELED_TABLES:
        if reflected and compare_to is None:
            return False
        if not reflected and compare_to is None:
            return False

    if type_ in {"index", "unique_constraint"}:
        return False

    return True


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=False,
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
            compare_server_default=False,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
