from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import (
    Session,
    joinedload,
)

from app.modules.transactions.models import (
    BusinessTransaction,
)


class TransactionRepository:
    def get_by_id(
        self,
        db: Session,
        transaction_id: int,
        tenant_id: int,
        for_update: bool = False,
    ) -> Optional[BusinessTransaction]:
        query = (
            db.query(BusinessTransaction)
            .options(
                joinedload(
                    BusinessTransaction.events
                )
            )
            .filter(
                BusinessTransaction.id
                == transaction_id,
                BusinessTransaction.tenant_id
                == tenant_id,
            )
        )

        if for_update:
            query = query.with_for_update()

        return query.first()

    def get_by_number(
        self,
        db: Session,
        transaction_number: str,
        tenant_id: int,
        for_update: bool = False,
    ) -> Optional[BusinessTransaction]:
        query = (
            db.query(BusinessTransaction)
            .options(
                joinedload(
                    BusinessTransaction.events
                )
            )
            .filter(
                BusinessTransaction.tenant_id
                == tenant_id,
                BusinessTransaction
                .transaction_number
                == transaction_number,
            )
        )

        if for_update:
            query = query.with_for_update()

        return query.first()

    def find_by_source(
        self,
        db: Session,
        tenant_id: int,
        source_module: str,
        source_entity: str,
        source_id: int,
    ) -> Optional[BusinessTransaction]:
        return (
            db.query(BusinessTransaction)
            .filter(
                BusinessTransaction.tenant_id
                == tenant_id,
                BusinessTransaction.source_module
                == source_module,
                BusinessTransaction.source_entity
                == source_entity,
                BusinessTransaction.source_id
                == source_id,
            )
            .first()
        )

    def list_transactions(
        self,
        db: Session,
        tenant_id: int,
        page: int,
        page_size: int,
        company_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        transaction_status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[
        list[BusinessTransaction],
        int,
    ]:
        query = (
            db.query(BusinessTransaction)
            .options(
                joinedload(
                    BusinessTransaction.events
                )
            )
            .filter(
                BusinessTransaction.tenant_id
                == tenant_id
            )
        )

        if company_id is not None:
            query = query.filter(
                BusinessTransaction.company_id
                == company_id
            )

        if branch_id is not None:
            query = query.filter(
                BusinessTransaction.branch_id
                == branch_id
            )

        if transaction_type:
            query = query.filter(
                BusinessTransaction.transaction_type
                == transaction_type
            )

        if transaction_status:
            query = query.filter(
                BusinessTransaction.status
                == transaction_status
            )

        if search:
            search_value = (
                f"%{search.strip()}%"
            )

            query = query.filter(
                or_(
                    BusinessTransaction
                    .transaction_number
                    .ilike(search_value),
                    BusinessTransaction
                    .document_number
                    .ilike(search_value),
                    BusinessTransaction
                    .reference_number
                    .ilike(search_value),
                    BusinessTransaction
                    .external_reference
                    .ilike(search_value),
                )
            )

        total = query.count()

        items = (
            query
            .order_by(
                BusinessTransaction
                .created_at
                .desc()
            )
            .offset(
                (page - 1) * page_size
            )
            .limit(page_size)
            .all()
        )

        return items, total

    def add(
        self,
        db: Session,
        transaction: BusinessTransaction,
    ) -> BusinessTransaction:
        db.add(transaction)
        db.flush()

        return transaction


transaction_repository = (
    TransactionRepository()
)