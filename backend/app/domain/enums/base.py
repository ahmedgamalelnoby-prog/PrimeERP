from __future__ import annotations

try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        """
        Compatibility implementation for Python 3.10.
        """

        def __str__(self) -> str:
            return str(self.value)