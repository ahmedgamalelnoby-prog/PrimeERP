from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from .models import Feature
from .schemas import FeatureCreate, FeatureUpdate


class FeatureRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        feature_id: int,
        *,
        include_deleted: bool = False,
    ) -> Feature | None:
        statement = select(Feature).where(
            Feature.id == feature_id
        )

        if not include_deleted:
            statement = statement.where(
                Feature.is_deleted.is_(False)
            )

        return self.db.scalar(statement)

    def get_by_code(
        self,
        code: str,
        *,
        include_deleted: bool = False,
    ) -> Feature | None:
        statement = select(Feature).where(
            Feature.code == code.strip().lower()
        )

        if not include_deleted:
            statement = statement.where(
                Feature.is_deleted.is_(False)
            )

        return self.db.scalar(statement)

    def code_exists(
        self,
        code: str,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        statement = select(func.count(Feature.id)).where(
            Feature.code == code.strip().lower(),
            Feature.is_deleted.is_(False),
        )

        if exclude_id is not None:
            statement = statement.where(
                Feature.id != exclude_id
            )

        return bool(self.db.scalar(statement))

    def list(
        self,
        *,
        search: str | None = None,
        category: str | None = None,
        feature_type: str | None = None,
        status: str | None = None,
        is_core: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Feature], int]:
        filters = [
            Feature.is_deleted.is_(False),
        ]

        if search:
            search_value = f"%{search.strip()}%"

            filters.append(
                or_(
                    Feature.code.ilike(search_value),
                    Feature.name.ilike(search_value),
                    Feature.name_ar.ilike(search_value),
                    Feature.display_name.ilike(search_value),
                )
            )

        if category:
            filters.append(
                Feature.category == category
            )

        if feature_type:
            filters.append(
                Feature.feature_type == feature_type
            )

        if status:
            filters.append(
                Feature.status == status
            )

        if is_core is not None:
            filters.append(
                Feature.is_core == is_core
            )

        total_statement = select(
            func.count(Feature.id)
        ).where(*filters)

        total = self.db.scalar(total_statement) or 0

        statement: Select[tuple[Feature]] = (
            select(Feature)
            .where(*filters)
            .order_by(
                Feature.sort_order.asc(),
                Feature.code.asc(),
            )
            .offset(offset)
            .limit(limit)
        )

        items = list(
            self.db.scalars(statement).all()
        )

        return items, total

    def create(
        self,
        data: FeatureCreate,
    ) -> Feature:
        payload = data.model_dump(mode="json")

        feature = Feature(**payload)

        self.db.add(feature)
        self.db.flush()
        self.db.refresh(feature)

        return feature

    def update(
        self,
        feature: Feature,
        data: FeatureUpdate,
    ) -> Feature:
        payload = data.model_dump(
            exclude_unset=True,
            mode="json",
        )

        for field_name, value in payload.items():
            setattr(feature, field_name, value)

        self.db.add(feature)
        self.db.flush()
        self.db.refresh(feature)

        return feature

    def soft_delete(
        self,
        feature: Feature,
        *,
        deleted_by: int | None = None,
    ) -> Feature:
        from datetime import datetime, timezone

        feature.is_deleted = True
        feature.deleted_at = datetime.now(timezone.utc)
        feature.deleted_by = deleted_by
        feature.is_active = False

        self.db.add(feature)
        self.db.flush()
        self.db.refresh(feature)

        return feature

    def restore(
        self,
        feature: Feature,
    ) -> Feature:
        feature.is_deleted = False
        feature.deleted_at = None
        feature.deleted_by = None
        feature.is_active = True

        self.db.add(feature)
        self.db.flush()
        self.db.refresh(feature)

        return feature