from __future__ import annotations

from sqlalchemy.orm import Session

from .constants import FeatureType, FeatureValueType
from .exceptions import (
    CoreFeatureModificationError,
    FeatureCodeAlreadyExistsError,
    FeatureNotFoundError,
    InvalidFeatureValueError,
)
from .models import Feature
from .repository import FeatureRepository
from .schemas import FeatureCreate, FeatureUpdate
from .validators import normalize_feature_value


class FeatureService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = FeatureRepository(db)

    def get_feature(
        self,
        feature_id: int,
    ) -> Feature:
        feature = self.repository.get_by_id(feature_id)

        if feature is None:
            raise FeatureNotFoundError(feature_id)

        return feature

    def get_feature_by_code(
        self,
        code: str,
    ) -> Feature:
        feature = self.repository.get_by_code(code)

        if feature is None:
            raise FeatureNotFoundError(code)

        return feature

    def list_features(
        self,
        *,
        search: str | None = None,
        category: str | None = None,
        feature_type: str | None = None,
        status: str | None = None,
        is_core: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Feature], int]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 200)

        offset = (page - 1) * page_size

        return self.repository.list(
            search=search,
            category=category,
            feature_type=feature_type,
            status=status,
            is_core=is_core,
            offset=offset,
            limit=page_size,
        )

    def create_feature(
        self,
        data: FeatureCreate,
    ) -> Feature:
        if self.repository.code_exists(data.code):
            raise FeatureCodeAlreadyExistsError(data.code)

        normalized_default_value = self._validate_default_value(
            feature_type=data.feature_type,
            value_type=data.value_type,
            default_value=data.default_value,
        )

        payload = data.model_copy(
            update={
                "default_value": normalized_default_value,
            }
        )

        try:
            feature = self.repository.create(payload)
            self.db.commit()
            self.db.refresh(feature)
            return feature

        except Exception:
            self.db.rollback()
            raise

    def update_feature(
        self,
        feature_id: int,
        data: FeatureUpdate,
    ) -> Feature:
        feature = self.get_feature(feature_id)

        payload = data.model_dump(exclude_unset=True)

        resulting_feature_type = payload.get(
            "feature_type",
            feature.feature_type,
        )

        resulting_value_type = payload.get(
            "value_type",
            feature.value_type,
        )

        resulting_default_value = payload.get(
            "default_value",
            feature.default_value,
        )

        if {
            "feature_type",
            "value_type",
            "default_value",
        }.intersection(payload):
            normalized_default_value = self._validate_default_value(
                feature_type=resulting_feature_type,
                value_type=resulting_value_type,
                default_value=resulting_default_value,
            )

            data = data.model_copy(
                update={
                    "default_value": normalized_default_value,
                }
            )

        try:
            feature = self.repository.update(
                feature,
                data,
            )

            self.db.commit()
            self.db.refresh(feature)

            return feature

        except Exception:
            self.db.rollback()
            raise

    def delete_feature(
        self,
        feature_id: int,
        *,
        deleted_by: int | None = None,
    ) -> Feature:
        feature = self.get_feature(feature_id)

        if feature.is_core:
            raise CoreFeatureModificationError(feature.code)

        try:
            feature = self.repository.soft_delete(
                feature,
                deleted_by=deleted_by,
            )

            self.db.commit()
            self.db.refresh(feature)

            return feature

        except Exception:
            self.db.rollback()
            raise

    def restore_feature(
        self,
        feature_id: int,
    ) -> Feature:
        feature = self.repository.get_by_id(
            feature_id,
            include_deleted=True,
        )

        if feature is None:
            raise FeatureNotFoundError(feature_id)

        try:
            feature = self.repository.restore(feature)

            self.db.commit()
            self.db.refresh(feature)

            return feature

        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _validate_default_value(
        *,
        feature_type: FeatureType | str,
        value_type: FeatureValueType | str,
        default_value: str | None,
    ) -> str | None:
        normalized_feature_type = FeatureType(feature_type)
        normalized_value_type = FeatureValueType(value_type)

        if normalized_feature_type == FeatureType.LIMIT:
            if normalized_value_type not in {
                FeatureValueType.INTEGER,
                FeatureValueType.DECIMAL,
            }:
                raise InvalidFeatureValueError(
                    "Limit features must use integer or decimal values."
                )

        if default_value is None:
            if normalized_value_type == FeatureValueType.BOOLEAN:
                return "false"

            return None

        try:
            return normalize_feature_value(
                normalized_value_type,
                default_value,
            )

        except ValueError as exc:
            raise InvalidFeatureValueError(
                str(exc)
            ) from exc