from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from app.core.database import UnitOfWork

RepositoryType = TypeVar("RepositoryType")


class BaseService(Generic[RepositoryType]):
    """
    Base application service.

    Provides:
    - Database session
    - Current user
    - Current tenant
    - UnitOfWork
    - Repository
    """

    def __init__(
        self,
        *,
        repository: RepositoryType | None = None,
        db: Session | None = None,
        current_user: Any | None = None,
        current_tenant: Any | None = None,
    ) -> None:
        self.repository = repository
        self.db = db
        self.current_user = current_user
        self.current_tenant = current_tenant

    @property
    def uow(self) -> UnitOfWork:
        return UnitOfWork(session=self.require_db())

    def require_db(self) -> Session:
        if self.db is None:
            raise RuntimeError("Database session is required.")
        return self.db

    def require_repository(self) -> RepositoryType:
        if self.repository is None:
            raise RuntimeError("Repository is required.")
        return self.repository

    def require_current_user(self) -> Any:
        if self.current_user is None:
            raise RuntimeError("Current user is required.")
        return self.current_user

    def require_current_tenant(self) -> Any:
        if self.current_tenant is None:
            raise RuntimeError("Current tenant is required.")
        return self.current_tenant