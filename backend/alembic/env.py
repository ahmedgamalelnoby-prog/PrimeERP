from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# إضافة مجلد backend إلى Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.database.base import Base

# تحميل جميع الـ Models حتى يتعرف عليها Alembic
from app.core.config import settings
from app.database.base import Base

# Import all models so Alembic can load Base.metadata
from app.database import models  # noqa: F401

from app.modules.platform.features.models import Feature

# فعّل هذه الاستيرادات فقط إذا كانت الملفات موجودة فعليًا
try:
    from app.modules.companies.models import Company
except ImportError:
    Company = None

try:
    from app.modules.branches.models import Branch
except ImportError:
    Branch = None


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# الـ MetaData التي يقارنها Alembic بقاعدة البيانات
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(
        config.config_ini_section
    ) or {}

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
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
