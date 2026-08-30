from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class CodeMixin:
    """
    Business code.
    """

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )