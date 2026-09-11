from __future__ import annotations

from types import TracebackType
from typing import Callable, Type

from sqlalchemy.orm import Session


SessionFactory = Callable[[], Session]


class UnitOfWork:
    """
    Controls a single SQLAlchemy database transaction.

    The session factory is resolved lazily when the UnitOfWork starts its own
    session. This is intentional: importing SessionLocal at module import time
    can participate in a circular import while the ORM model registry is being
    initialized.
    """

    def __init__(
        self,
        *,
        session: Session | None = None,
        session_factory: SessionFactory | None = None,
    ) -> None:
        self._provided_session = session
        self._session_factory = session_factory

        self.session: Session | None = None
        self._owns_session = False
        self._committed = False

    def __enter__(self) -> "UnitOfWork":
        if self._provided_session is not None:
            self.session = self._provided_session
            self._owns_session = False
        else:
            if self._session_factory is None:
                from app.database.session import SessionLocal

                self._session_factory = SessionLocal

            self.session = self._session_factory()
            self._owns_session = True

        self._committed = False
        return self

    def commit(self) -> None:
        session = self._require_session()
        session.commit()
        self._committed = True

    def rollback(self) -> None:
        session = self._require_session()
        session.rollback()
        self._committed = False

    def flush(self) -> None:
        self._require_session().flush()

    def refresh(self, instance: object) -> None:
        self._require_session().refresh(instance)

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if self.session is None:
            return False

        try:
            if exc_type is not None or not self._committed:
                self.session.rollback()
        finally:
            if self._owns_session:
                self.session.close()

            self.session = None
            self._owns_session = False
            self._committed = False

        return False

    def _require_session(self) -> Session:
        if self.session is None:
            raise RuntimeError(
                "UnitOfWork session has not been started. "
                "Use it inside a 'with UnitOfWork(...)' block."
            )

        return self.session
