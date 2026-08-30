from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class VersionMixin:
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    @declared_attr.directive
    def __mapper_args__(cls) -> dict:
        return {
            "version_id_col": cls.version,
        }