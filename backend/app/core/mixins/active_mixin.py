from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column


class ActiveMixin:
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )