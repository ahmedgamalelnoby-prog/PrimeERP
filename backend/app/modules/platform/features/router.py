from math import ceil

from fastapi import APIRouter, HTTPException, Query, status

from .constants import (
    FeatureCategory,
    FeatureStatus,
    FeatureType,
)
from .dependencies import FeatureServiceDependency
from .exceptions import (
    CoreFeatureModificationError,
    FeatureCodeAlreadyExistsError,
    FeatureNotFoundError,
    InvalidFeatureValueError,
)
from .schemas import (
    FeatureCreate,
    FeatureListItem,
    FeatureRead,
    FeatureUpdate,
)


router = APIRouter(
    prefix="/features",
    tags=["Platform - Features"],
)


@router.get("")
def list_features(
    service: FeatureServiceDependency,
    search: str | None = Query(
        default=None,
        max_length=150,
    ),
    category: FeatureCategory | None = None,
    feature_type: FeatureType | None = None,
    feature_status: FeatureStatus | None = Query(
        default=None,
        alias="status",
    ),
    is_core: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    items, total = service.list_features(
        search=search,
        category=category.value if category else None,
        feature_type=(
            feature_type.value
            if feature_type
            else None
        ),
        status=(
            feature_status.value
            if feature_status
            else None
        ),
        is_core=is_core,
        page=page,
        page_size=page_size,
    )

    return {
        "items": [
            FeatureListItem.model_validate(item)
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if total else 0,
    }


@router.get(
    "/{feature_id}",
    response_model=FeatureRead,
)
def get_feature(
    feature_id: int,
    service: FeatureServiceDependency,
):
    try:
        return service.get_feature(feature_id)

    except FeatureNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=FeatureRead,
    status_code=status.HTTP_201_CREATED,
)
def create_feature(
    data: FeatureCreate,
    service: FeatureServiceDependency,
):
    try:
        return service.create_feature(data)

    except FeatureCodeAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except InvalidFeatureValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{feature_id}",
    response_model=FeatureRead,
)
def update_feature(
    feature_id: int,
    data: FeatureUpdate,
    service: FeatureServiceDependency,
):
    try:
        return service.update_feature(
            feature_id,
            data,
        )

    except FeatureNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidFeatureValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{feature_id}",
    response_model=FeatureRead,
)
def delete_feature(
    feature_id: int,
    service: FeatureServiceDependency,
):
    try:
        return service.delete_feature(feature_id)

    except FeatureNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except CoreFeatureModificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{feature_id}/restore",
    response_model=FeatureRead,
)
def restore_feature(
    feature_id: int,
    service: FeatureServiceDependency,
):
    try:
        return service.restore_feature(feature_id)

    except FeatureNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc