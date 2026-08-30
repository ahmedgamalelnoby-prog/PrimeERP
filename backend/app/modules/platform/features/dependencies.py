from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from .service import FeatureService


def get_feature_service(
    db: Annotated[Session, Depends(get_db)],
) -> FeatureService:
    return FeatureService(db)


FeatureServiceDependency = Annotated[
    FeatureService,
    Depends(get_feature_service),
]