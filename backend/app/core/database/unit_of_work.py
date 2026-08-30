from __future__ import annotations

from types import TracebackType
from typing import Callable, Type

from sqlalchemy.orm import Session

from app.database.session import SessionLocal


SessionFactory = Callable[[], Session]


class UnitOfWork:
    """
    Controls a single database transaction.

    The UnitOfWork can either:

    1. Use an existing SQLAlchemy session supplied by FastAPI.
    2. Create and own a new session using SessionLocal.

    Transactions are explicit:
    - commit() must be called when the operation succeeds.
    - rollback happens automatically when an exception occurs.
    - an uncommitted transaction is rolled back when leaving the context.
    """

    def __init__(
        self,
        *,
        session: Session | None = None,
        session_factory: SessionFactory = SessionLocal,
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
            if exc_type is not None:
                self.session.rollback()

            elif not self._committed:
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