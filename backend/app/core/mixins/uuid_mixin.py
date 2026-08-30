from uuid import UUID as PythonUUID
from uuid import uuid4

from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    uuid: Mapped[PythonUUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        default=uuid4,
        nullable=False,
        unique=True,
        index=True,
    )