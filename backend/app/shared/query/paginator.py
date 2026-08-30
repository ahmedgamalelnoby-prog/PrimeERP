from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.shared.query.request import QueryRequest
from app.shared.query.response import QueryResponse

T = TypeVar("T")


class SQLAlchemyPaginator(Generic[T]):

    def paginate(
        self,
        *,
        db: Session,
        query,
        request: QueryRequest,
    ) -> QueryResponse[T]:

        ...