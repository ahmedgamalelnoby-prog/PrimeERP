from typing import Optional

from sqlalchemy.orm import Session

from app.modules.transactions.models import (
    NumberSequence,
)


class NumberSequenceRepository:
    def get_by_id(
        self,
        db: Session,
        sequence_id: int,
    ) -> Optional[NumberSequence]:
        return (
            db.query(NumberSequence)
            .filter(
                NumberSequence.id
                == sequence_id
            )
            .first()
        )

    def get_by_scope(
        self,
        db: Session,
        tenant_id: int,
        company_id: int,
        branch_id: int,
        sequence_key: str,
        for_update: bool = False,
    ) -> Optional[NumberSequence]:
        query = (
            db.query(NumberSequence)
            .filter(
                NumberSequence.tenant_id
                == tenant_id,
                NumberSequence.company_id
                == company_id,
                NumberSequence.branch_id
                == branch_id,
                NumberSequence.sequence_key
                == sequence_key,
            )
        )

        if for_update:
            query = query.with_for_update()

        return query.first()

    def list_by_tenant(
        self,
        db: Session,
        tenant_id: int,
        company_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> list[NumberSequence]:
        query = (
            db.query(NumberSequence)
            .filter(
                NumberSequence.tenant_id
                == tenant_id
            )
        )

        if company_id is not None:
            query = query.filter(
                NumberSequence.company_id
                == company_id
            )

        if branch_id is not None:
            query = query.filter(
                NumberSequence.branch_id
                == branch_id
            )

        if is_active is not None:
            query = query.filter(
                NumberSequence.is_active
                == is_active
            )

        return (
            query
            .order_by(
                NumberSequence.sequence_key.asc()
            )
            .all()
        )

    def add(
        self,
        db: Session,
        sequence: NumberSequence,
    ) -> NumberSequence:
        db.add(sequence)
        db.flush()

        return sequence


number_sequence_repository = (
    NumberSequenceRepository()
)