from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.database.base import Base
from app.database import models  # noqa: F401

try:
    from app.modules.platform.features.models import Feature  # noqa: F401
except ImportError:
    Feature = None

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

MANAGED_SAAS_TABLES = {
    "platform_settings", "module_prices", "subscription_modules", "discounts",
    "offers", "coupons", "bank_accounts", "invoices", "payment_requests",
    "subscription_events",
}
LEGACY_TABLES = {"plans"}
MANAGED_INDEXES = {"ix_legal_acceptances_id", "ix_legal_documents_id"}


def include_object(object_, name, type_, reflected, compare_to):
    """Exclude explicitly migration-managed legacy objects from autogenerate."""
    if type_ == "index" and name in MANAGED_INDEXES:
        return False
    if type_ == "table" and reflected and compare_to is None:
        if name in MANAGED_SAAS_TABLES or name in LEGACY_TABLES:
            return False
    if type_ == "index" and reflected:
        table_name = getattr(object_.table, "name", None)
        if table_name in MANAGED_SAAS_TABLES or table_name in LEGACY_TABLES:
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
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
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
