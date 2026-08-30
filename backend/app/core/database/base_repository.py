from __future__ import annotations

from datetime import datetime, timezone
from typing import (
    Any,
    Generic,
    Iterable,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

from sqlalchemy import func, select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.database.base import Base
from app.shared.query import (
    QueryOptions,
    QueryRequest,
    QueryResponse,
    SQLAlchemyFilterAdapter,
    SQLAlchemyPaginator,
    SQLAlchemySearchAdapter,
    SQLAlchemySortingAdapter,
)

ModelType = TypeVar(
    "ModelType",
    bound=Base,
)

class BaseRepository(Generic[ModelType]):
    def __init__(
    self,
    model: Type[ModelType],
    query_options: QueryOptions | None = None,
) -> None:
        self.model = model

        self.filter_adapter = SQLAlchemyFilterAdapter()
        self.search_adapter = SQLAlchemySearchAdapter()
        self.sort_adapter = SQLAlchemySortingAdapter()
        self.paginator = SQLAlchemyPaginator()

        self.query_options = query_options or QueryOptions()

    def get_by_id(
        self,
        db: Session,
        record_id: int,
        *,
        for_update: bool = False,
    ) -> Optional[ModelType]:
        query = select(self.model).where(
            self.model.id == record_id
        )

        if for_update:
            query = query.with_for_update()

        return db.execute(
            query
        ).scalar_one_or_none()

    def get_by_uuid(
        self,
        db: Session,
        record_uuid: Any,
        *,
        for_update: bool = False,
    ) -> Optional[ModelType]:
        if not hasattr(
            self.model,
            "uuid",
        ):
            raise AttributeError(
                f"{self.model.__name__} does not contain a uuid column"
            )

        query = select(self.model).where(
            self.model.uuid == record_uuid
        )

        if for_update:
            query = query.with_for_update()

        return db.execute(
            query
        ).scalar_one_or_none()

    def get_first(
        self,
        db: Session,
        **filters: Any,
    ) -> Optional[ModelType]:
        query = select(self.model)

        query = self._apply_filters(
            query,
            filters,
        )

        return db.execute(
            query.limit(1)
        ).scalar_one_or_none()

    def list(
        self,
        db: Session,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None,
        **filters: Any,
    ) -> list[ModelType]:
        query = select(self.model)

        query = self._apply_filters(
            query,
            filters,
        )

        if order_by is not None:
            query = query.order_by(
                order_by
            )

        query = query.offset(
            offset
        ).limit(
            limit
        )
        
        return list(
            db.execute(
                query
            ).scalars().all()
        )
    
    def query(
        self,
        db: Session,
        request: QueryRequest,
    ) -> QueryResponse[ModelType]:
        query = select(self.model)

        query = self.filter_adapter.apply(
            query=query,
            model=self.model,
            filters=request.filters,
            allowed_fields=self.query_options.filterable_fields,
        )

        query = self.search_adapter.apply(
            query=query,
            model=self.model,
            search=request.search,
            search_fields=self.query_options.searchable_fields,
        )

        query = self.sort_adapter.apply(
            query=query,
            model=self.model,
            sort=request.sort,
            allowed_fields=self.query_options.sortable_fields,
        )

        return self.paginator.paginate(
            db=db,
            query=query,
            request=request,
        )

    def count(
        self,
        db: Session,
        **filters: Any,
    ) -> int:
        query = select(
            func.count()
        ).select_from(
            self.model
        )

        query = self._apply_filters(
            query,
            filters,
        )

        return int(
            db.execute(
                query
            ).scalar_one()
        )

    def exists(
        self,
        db: Session,
        **filters: Any,
    ) -> bool:
        query = select(
            self.model.id
        )

        query = self._apply_filters(
            query,
            filters,
        ).limit(1)

        return (
            db.execute(
                query
            ).scalar_one_or_none()
            is not None
        )

    def create(
        self,
        db: Session,
        *,
        data: dict[str, Any],
        flush: bool = True,
    ) -> ModelType:
        instance = self.model(
            **data
        )

        db.add(instance)

        if flush:
            db.flush()

        return instance

    def add(
        self,
        db: Session,
        instance: ModelType,
        *,
        flush: bool = True,
    ) -> ModelType:
        db.add(instance)

        if flush:
            db.flush()

        return instance

    def add_all(
        self,
        db: Session,
        instances: Iterable[ModelType],
        *,
        flush: bool = True,
    ) -> Sequence[ModelType]:
        records = list(
            instances
        )

        db.add_all(records)

        if flush:
            db.flush()

        return records

    def update(
        self,
        db: Session,
        instance: ModelType,
        *,
        data: dict[str, Any],
        flush: bool = True,
    ) -> ModelType:
        model_columns = {
            attribute.key
            for attribute in inspect(
                self.model
            ).mapper.column_attrs
        }

        protected_fields = {
            "id",
            "uuid",
            "created_at",
            "created_by",
        }

        for field_name, value in data.items():
            if field_name not in model_columns:
                raise AttributeError(
                    f"{self.model.__name__} does not contain field {field_name!r}"
                )

            if field_name in protected_fields:
                continue

            setattr(
                instance,
                field_name,
                value,
            )

        db.add(instance)

        if flush:
            db.flush()

        return instance

    def delete(
        self,
        db: Session,
        instance: ModelType,
        *,
        flush: bool = True,
    ) -> None:
        db.delete(instance)

        if flush:
            db.flush()

    def soft_delete(
        self,
        db: Session,
        instance: ModelType,
        *,
        deleted_by: Optional[int] = None,
        flush: bool = True,
    ) -> ModelType:
        if not hasattr(
            instance,
            "is_deleted",
        ):
            raise AttributeError(
                f"{self.model.__name__} does not support soft delete"
            )

        instance.is_deleted = True

        if hasattr(
            instance,
            "deleted_at",
        ):
            instance.deleted_at = datetime.now(
                timezone.utc
            )

        if hasattr(
            instance,
            "deleted_by",
        ):
            instance.deleted_by = deleted_by

        db.add(instance)

        if flush:
            db.flush()

        return instance

    def restore(
        self,
        db: Session,
        instance: ModelType,
        *,
        flush: bool = True,
    ) -> ModelType:
        if not hasattr(
            instance,
            "is_deleted",
        ):
            raise AttributeError(
                f"{self.model.__name__} does not support restore"
            )

        instance.is_deleted = False

        if hasattr(
            instance,
            "deleted_at",
        ):
            instance.deleted_at = None

        if hasattr(
            instance,
            "deleted_by",
        ):
            instance.deleted_by = None

        db.add(instance)

        if flush:
            db.flush()

        return instance

    def refresh(
        self,
        db: Session,
        instance: ModelType,
    ) -> ModelType:
        db.refresh(instance)

        return instance

    def flush(
        self,
        db: Session,
    ) -> None:
        db.flush()

    def _apply_filters(
        self,
        query: Any,
        filters: dict[str, Any],
    ) -> Any:
        for field_name, value in filters.items():
            if value is None:
                continue

            if not hasattr(
                self.model,
                field_name,
            ):
                raise AttributeError(
                    f"{self.model.__name__} does not contain filter {field_name!r}"
                )

            model_field = getattr(
                self.model,
                field_name,
            )

            query = query.where(
                model_field == value
            )

        return query