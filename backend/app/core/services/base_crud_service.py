from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

from app.core.database.base_repository import BaseRepository
from app.database.base import Base
from app.shared.query import QueryRequest, QueryResponse


ModelType = TypeVar(
    "ModelType",
    bound=Base,
)

RepositoryType = TypeVar(
    "RepositoryType",
    bound=BaseRepository[Any],
)


class BaseCRUDService(
    Generic[ModelType, RepositoryType]
):
    """
    Base service for common CRUD operations.

    Database commits are intentionally not performed here.
    Transaction management should remain at the request,
    unit-of-work, or dependency layer.
    """

    def __init__(
        self,
        repository: RepositoryType,
    ) -> None:
        self.repository = repository

    def get_by_id(
        self,
        db: Session,
        record_id: int,
        *,
        for_update: bool = False,
    ) -> ModelType | None:
        return self.repository.get_by_id(
            db,
            record_id,
            for_update=for_update,
        )

    def get_by_uuid(
        self,
        db: Session,
        record_uuid: Any,
        *,
        for_update: bool = False,
    ) -> ModelType | None:
        return self.repository.get_by_uuid(
            db,
            record_uuid,
            for_update=for_update,
        )

    def get_first(
        self,
        db: Session,
        **filters: Any,
    ) -> ModelType | None:
        return self.repository.get_first(
            db,
            **filters,
        )

    def list(
        self,
        db: Session,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Any | None = None,
        **filters: Any,
    ) -> list[ModelType]:
        return self.repository.list(
            db,
            offset=offset,
            limit=limit,
            order_by=order_by,
            **filters,
        )

    def query(
        self,
        db: Session,
        request: QueryRequest,
    ) -> QueryResponse[ModelType]:
        return self.repository.query(
            db,
            request,
        )

    def count(
        self,
        db: Session,
        **filters: Any,
    ) -> int:
        return self.repository.count(
            db,
            **filters,
        )

    def exists(
        self,
        db: Session,
        **filters: Any,
    ) -> bool:
        return self.repository.exists(
            db,
            **filters,
        )

    def create(
        self,
        db: Session,
        data: Any,
        *,
        flush: bool = True,
    ) -> ModelType:
        payload = self._to_dict(
            data,
        )

        payload = self.before_create(
            db,
            payload,
        )

        instance = self.repository.create(
            db,
            data=payload,
            flush=flush,
        )

        instance = self.after_create(
            db,
            instance,
        )

        return instance

    def update(
        self,
        db: Session,
        instance: ModelType,
        data: Any,
        *,
        flush: bool = True,
    ) -> ModelType:
        payload = self._to_dict(
            data,
            exclude_unset=True,
        )

        payload = self.before_update(
            db,
            instance,
            payload,
        )

        updated_instance = self.repository.update(
            db,
            instance,
            data=payload,
            flush=flush,
        )

        updated_instance = self.after_update(
            db,
            updated_instance,
        )

        return updated_instance

    def delete(
        self,
        db: Session,
        instance: ModelType,
        *,
        flush: bool = True,
    ) -> None:
        self.before_delete(
            db,
            instance,
        )

        self.repository.delete(
            db,
            instance,
            flush=flush,
        )

        self.after_delete(
            db,
            instance,
        )

    def soft_delete(
        self,
        db: Session,
        instance: ModelType,
        *,
        deleted_by: int | None = None,
        flush: bool = True,
    ) -> ModelType:
        self.before_soft_delete(
            db,
            instance,
        )

        deleted_instance = self.repository.soft_delete(
            db,
            instance,
            deleted_by=deleted_by,
            flush=flush,
        )

        deleted_instance = self.after_soft_delete(
            db,
            deleted_instance,
        )

        return deleted_instance

    def restore(
        self,
        db: Session,
        instance: ModelType,
        *,
        flush: bool = True,
    ) -> ModelType:
        self.before_restore(
            db,
            instance,
        )

        restored_instance = self.repository.restore(
            db,
            instance,
            flush=flush,
        )

        restored_instance = self.after_restore(
            db,
            restored_instance,
        )

        return restored_instance

    def refresh(
        self,
        db: Session,
        instance: ModelType,
    ) -> ModelType:
        return self.repository.refresh(
            db,
            instance,
        )

    def before_create(
        self,
        db: Session,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return data

    def after_create(
        self,
        db: Session,
        instance: ModelType,
    ) -> ModelType:
        return instance

    def before_update(
        self,
        db: Session,
        instance: ModelType,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return data

    def after_update(
        self,
        db: Session,
        instance: ModelType,
    ) -> ModelType:
        return instance

    def before_delete(
        self,
        db: Session,
        instance: ModelType,
    ) -> None:
        return None

    def after_delete(
        self,
        db: Session,
        instance: ModelType,
    ) -> None:
        return None

    def before_soft_delete(
        self,
        db: Session,
        instance: ModelType,
    ) -> None:
        return None

    def after_soft_delete(
        self,
        db: Session,
        instance: ModelType,
    ) -> ModelType:
        return instance

    def before_restore(
        self,
        db: Session,
        instance: ModelType,
    ) -> None:
        return None

    def after_restore(
        self,
        db: Session,
        instance: ModelType,
    ) -> ModelType:
        return instance

    @staticmethod
    def _to_dict(
        data: Any,
        *,
        exclude_unset: bool = False,
    ) -> dict[str, Any]:
        if isinstance(
            data,
            dict,
        ):
            return dict(data)

        if hasattr(
            data,
            "model_dump",
        ):
            return data.model_dump(
                exclude_unset=exclude_unset,
            )

        if hasattr(
            data,
            "dict",
        ):
            return data.dict(
                exclude_unset=exclude_unset,
            )

        raise TypeError(
            "Data must be a dictionary or a Pydantic model."
        )