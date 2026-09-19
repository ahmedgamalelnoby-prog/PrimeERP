from datetime import (
    date,
    datetime,
    timezone,
)
from math import ceil
from typing import Optional

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.identity.models import User
from app.modules.transactions.models import (
    BusinessTransaction,
    TransactionEvent,
)
from app.modules.transactions.lifecycle import LifecycleError, validate_transaction_transition
from app.modules.transactions.repositories.transaction_repository import (
    transaction_repository,
)
from app.modules.transactions.schemas import (
    TransactionCreate,
    TransactionUpdate,
)
from app.modules.transactions.services.numbering_service import (
    numbering_service,
)


class TransactionService:
    def create_transaction(
        self,
        db: Session,
        payload: TransactionCreate,
        current_user: User,
    ) -> BusinessTransaction:
        tenant_id = self._get_tenant_id(
            current_user
        )

        self._validate_scope(
            db=db,
            tenant_id=tenant_id,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
        )

        if payload.source_id is not None:
            existing = (
                transaction_repository
                .find_by_source(
                    db=db,
                    tenant_id=tenant_id,
                    source_module=(
                        payload.source_module
                    ),
                    source_entity=(
                        payload.source_entity
                    ),
                    source_id=payload.source_id,
                )
            )

            if existing is not None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "A transaction already exists "
                        "for this source record"
                    ),
                )

        try:
            number_result = (
                numbering_service
                .generate_next_number(
                    db=db,
                    tenant_id=tenant_id,
                    company_id=payload.company_id,
                    branch_id=payload.branch_id,
                    sequence_key="TRANSACTION",
                    commit=False,
                )
            )

            transaction = BusinessTransaction(
                tenant_id=tenant_id,
                company_id=payload.company_id,
                branch_id=payload.branch_id,
                transaction_number=(
                    number_result[
                        "generated_number"
                    ]
                ),
                transaction_type=(
                    payload.transaction_type
                ),
                document_number=(
                    payload.document_number
                ),
                status="draft",
                source_module=(
                    payload.source_module
                ),
                source_entity=(
                    payload.source_entity
                ),
                source_id=payload.source_id,
                reference_number=(
                    payload.reference_number
                ),
                external_reference=(
                    payload.external_reference
                ),
                transaction_date=(
                    payload.transaction_date
                ),
                metadata_json=(
                    payload.metadata_json
                ),
                created_by=current_user.id,
                is_cancelled=False,
                is_reversed=False,
            )

            transaction_repository.add(
                db=db,
                transaction=transaction,
            )

            self._add_event(
                db=db,
                transaction=transaction,
                event_type="created",
                previous_status=None,
                new_status="draft",
                description=(
                    "Transaction created"
                ),
                performed_by=current_user.id,
            )

            db.commit()
            db.refresh(transaction)

            return self.get_by_id(
                db=db,
                transaction_id=transaction.id,
                current_user=current_user,
            )

        except HTTPException:
            db.rollback()
            raise

        except IntegrityError as exc:
            db.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Transaction number or source "
                    "already exists"
                ),
            ) from exc

        except Exception as exc:
            db.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Could not create transaction"
                ),
            ) from exc

    def update_transaction(
        self,
        db: Session,
        transaction_id: int,
        payload: TransactionUpdate,
        current_user: User,
    ) -> BusinessTransaction:
        transaction = self._get_locked(
            db=db,
            transaction_id=transaction_id,
            current_user=current_user,
        )

        if transaction.status != "draft":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only draft transactions "
                    "can be edited"
                ),
            )

        update_data = payload.model_dump(
            exclude_unset=True
        )

        for field_name, value in (
            update_data.items()
        ):
            setattr(
                transaction,
                field_name,
                value,
            )

        self._add_event(
            db=db,
            transaction=transaction,
            event_type="updated",
            previous_status="draft",
            new_status="draft",
            description=(
                "Transaction details updated"
            ),
            performed_by=current_user.id,
            event_data={
                "updated_fields": list(
                    update_data.keys()
                ),
            },
        )

        db.commit()
        db.refresh(transaction)

        return self.get_by_id(
            db=db,
            transaction_id=transaction.id,
            current_user=current_user,
        )

    def submit_transaction(
        self,
        db: Session,
        transaction_id: int,
        current_user: User,
        reason: Optional[str] = None,
    ) -> BusinessTransaction:
        return self._change_status(
            db=db,
            transaction_id=transaction_id,
            current_user=current_user,
            allowed_statuses={"draft"},
            new_status="pending",
            event_type="submitted",
            description=(
                reason
                or "Transaction submitted for approval"
            ),
        )

    def approve_transaction(
        self,
        db: Session,
        transaction_id: int,
        current_user: User,
        reason: Optional[str] = None,
    ) -> BusinessTransaction:
        transaction = self._get_locked(
            db=db,
            transaction_id=transaction_id,
            current_user=current_user,
        )

        try:
            validate_transaction_transition(
                transaction.status, "approved"
            )
        except LifecycleError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        previous_status = transaction.status

        transaction.status = "approved"
        transaction.approved_by = (
            current_user.id
        )
        transaction.approved_at = (
            datetime.now(timezone.utc)
        )

        self._add_event(
            db=db,
            transaction=transaction,
            event_type="approved",
            previous_status=previous_status,
            new_status="approved",
            description=(
                reason
                or "Transaction approved"
            ),
            performed_by=current_user.id,
        )

        db.commit()
        db.refresh(transaction)

        return self.get_by_id(
            db=db,
            transaction_id=transaction.id,
            current_user=current_user,
        )

    def post_transaction(
        self,
        db: Session,
        transaction_id: int,
        current_user: User,
        reason: Optional[str] = None,
    ) -> BusinessTransaction:
        transaction = self._get_locked(
            db=db,
            transaction_id=transaction_id,
            current_user=current_user,
        )

        try:
            validate_transaction_transition(
                transaction.status, "posted"
            )
        except LifecycleError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        previous_status = transaction.status

        transaction.status = "posted"
        transaction.posting_date = (
            date.today()
        )
        transaction.posted_by = (
            current_user.id
        )
        transaction.posted_at = (
            datetime.now(timezone.utc)
        )

        self._add_event(
            db=db,
            transaction=transaction,
            event_type="posted",
            previous_status=previous_status,
            new_status="posted",
            description=(
                reason
                or "Transaction posted"
            ),
            performed_by=current_user.id,
        )

        db.commit()
        db.refresh(transaction)

        return self.get_by_id(
            db=db,
            transaction_id=transaction.id,
            current_user=current_user,
        )

    def cancel_transaction(
        self,
        db: Session,
        transaction_number: str,
        reason: str,
        current_user: User,
    ) -> BusinessTransaction:
        tenant_id = self._get_tenant_id(
            current_user
        )

        transaction = (
            transaction_repository
            .get_by_number(
                db=db,
                transaction_number=(
                    transaction_number
                ),
                tenant_id=tenant_id,
                for_update=True,
            )
        )

        if transaction is None:
            self._raise_not_found()

        if transaction.status not in {
            "draft",
            "pending",
            "approved",
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Posted transactions cannot "
                    "be cancelled. Use reversal."
                ),
            )

        previous_status = (
            transaction.status
        )

        transaction.status = "cancelled"
        transaction.is_cancelled = True
        transaction.cancellation_reason = (
            reason
        )
        transaction.cancelled_by = (
            current_user.id
        )
        transaction.cancelled_at = (
            datetime.now(timezone.utc)
        )

        self._add_event(
            db=db,
            transaction=transaction,
            event_type="cancelled",
            previous_status=previous_status,
            new_status="cancelled",
            description=reason,
            performed_by=current_user.id,
        )

        db.commit()
        db.refresh(transaction)

        return self.get_by_id(
            db=db,
            transaction_id=transaction.id,
            current_user=current_user,
        )

    def reverse_transaction(
        self,
        db: Session,
        transaction_number: str,
        reason: str,
        current_user: User,
    ) -> BusinessTransaction:
        tenant_id = self._get_tenant_id(
            current_user
        )

        original = (
            transaction_repository
            .get_by_number(
                db=db,
                transaction_number=(
                    transaction_number
                ),
                tenant_id=tenant_id,
                for_update=True,
            )
        )

        if original is None:
            self._raise_not_found()

        if original.status != "posted":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only posted transactions "
                    "can be reversed"
                ),
            )

        if original.is_reversed:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Transaction has already "
                    "been reversed"
                ),
            )

        try:
            number_result = (
                numbering_service
                .generate_next_number(
                    db=db,
                    tenant_id=tenant_id,
                    company_id=original.company_id,
                    branch_id=original.branch_id,
                    sequence_key="TRANSACTION",
                    commit=False,
                )
            )

            reversal = BusinessTransaction(
                tenant_id=tenant_id,
                company_id=original.company_id,
                branch_id=original.branch_id,
                transaction_number=(
                    number_result[
                        "generated_number"
                    ]
                ),
                transaction_type=(
                    original.transaction_type
                ),
                document_number=None,
                status="posted",
                source_module=(
                    original.source_module
                ),
                source_entity=(
                    f"{original.source_entity}_reversal"
                ),
                source_id=original.source_id,
                reference_number=(
                    original.transaction_number
                ),
                transaction_date=date.today(),
                posting_date=date.today(),
                original_transaction_id=(
                    original.id
                ),
                cancellation_reason=reason,
                metadata_json={
                    "reversal_reason": reason,
                    "original_transaction_number": (
                        original.transaction_number
                    ),
                },
                created_by=current_user.id,
                approved_by=current_user.id,
                posted_by=current_user.id,
                approved_at=(
                    datetime.now(
                        timezone.utc
                    )
                ),
                posted_at=(
                    datetime.now(
                        timezone.utc
                    )
                ),
                is_cancelled=False,
                is_reversed=False,
            )

            transaction_repository.add(
                db=db,
                transaction=reversal,
            )

            original.status = "reversed"
            original.is_reversed = True
            original.reversal_transaction_id = (
                reversal.id
            )

            self._add_event(
                db=db,
                transaction=original,
                event_type="reversed",
                previous_status="posted",
                new_status="reversed",
                description=reason,
                performed_by=current_user.id,
                event_data={
                    "reversal_transaction_number": (
                        reversal.transaction_number
                    ),
                },
            )

            self._add_event(
                db=db,
                transaction=reversal,
                event_type="reversal_created",
                previous_status=None,
                new_status="posted",
                description=reason,
                performed_by=current_user.id,
                event_data={
                    "original_transaction_number": (
                        original.transaction_number
                    ),
                },
            )

            db.commit()
            db.refresh(reversal)

            return self.get_by_id(
                db=db,
                transaction_id=reversal.id,
                current_user=current_user,
            )

        except HTTPException:
            db.rollback()
            raise

        except Exception as exc:
            db.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Could not reverse transaction"
                ),
            ) from exc

    def get_by_id(
        self,
        db: Session,
        transaction_id: int,
        current_user: User,
    ) -> BusinessTransaction:
        tenant_id = self._get_tenant_id(
            current_user
        )

        transaction = (
            transaction_repository.get_by_id(
                db=db,
                transaction_id=transaction_id,
                tenant_id=tenant_id,
            )
        )

        if transaction is None:
            self._raise_not_found()

        return transaction

    def get_by_number(
        self,
        db: Session,
        transaction_number: str,
        current_user: User,
    ) -> BusinessTransaction:
        tenant_id = self._get_tenant_id(
            current_user
        )

        transaction = (
            transaction_repository
            .get_by_number(
                db=db,
                transaction_number=(
                    transaction_number
                ),
                tenant_id=tenant_id,
            )
        )

        if transaction is None:
            self._raise_not_found()

        return transaction

    def list_transactions(
        self,
        db: Session,
        current_user: User,
        page: int,
        page_size: int,
        company_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        transaction_status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        tenant_id = self._get_tenant_id(
            current_user
        )

        items, total = (
            transaction_repository
            .list_transactions(
                db=db,
                tenant_id=tenant_id,
                page=page,
                page_size=page_size,
                company_id=company_id,
                branch_id=branch_id,
                transaction_type=(
                    transaction_type
                ),
                transaction_status=(
                    transaction_status
                ),
                search=search,
            )
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (
                ceil(total / page_size)
                if total
                else 0
            ),
        }

    def _change_status(
        self,
        db: Session,
        transaction_id: int,
        current_user: User,
        allowed_statuses: set[str],
        new_status: str,
        event_type: str,
        description: str,
    ) -> BusinessTransaction:
        transaction = self._get_locked(
            db=db,
            transaction_id=transaction_id,
            current_user=current_user,
        )

        if transaction.status not in allowed_statuses:
            try:
                validate_transaction_transition(
                    transaction.status, new_status
                )
            except LifecycleError as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=str(exc),
                ) from exc

        previous_status = (
            transaction.status
        )

        transaction.status = new_status

        self._add_event(
            db=db,
            transaction=transaction,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            description=description,
            performed_by=current_user.id,
        )

        db.commit()
        db.refresh(transaction)

        return self.get_by_id(
            db=db,
            transaction_id=transaction.id,
            current_user=current_user,
        )

    def _get_locked(
        self,
        db: Session,
        transaction_id: int,
        current_user: User,
    ) -> BusinessTransaction:
        tenant_id = self._get_tenant_id(
            current_user
        )

        transaction = (
            transaction_repository.get_by_id(
                db=db,
                transaction_id=transaction_id,
                tenant_id=tenant_id,
                for_update=True,
            )
        )

        if transaction is None:
            self._raise_not_found()

        return transaction

    @staticmethod
    def _add_event(
        db: Session,
        transaction: BusinessTransaction,
        event_type: str,
        previous_status: Optional[str],
        new_status: Optional[str],
        description: Optional[str],
        performed_by: Optional[int],
        event_data: Optional[dict] = None,
    ) -> None:
        event = TransactionEvent(
            tenant_id=transaction.tenant_id,
            transaction_id=transaction.id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            description=description,
            event_data=event_data,
            performed_by=performed_by,
        )

        db.add(event)
        db.flush()

    @staticmethod
    def _get_tenant_id(
        current_user: User,
    ) -> int:
        if current_user.is_platform_admin:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Platform administrator has "
                    "no tenant context"
                ),
            )

        if current_user.tenant_id is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "User is not assigned "
                    "to a tenant"
                ),
            )

        return current_user.tenant_id

    @staticmethod
    def _validate_scope(
        db: Session,
        tenant_id: int,
        company_id: int,
        branch_id: int,
    ) -> None:
        company_exists = (
            db.query(Company.id)
            .filter(
                Company.id == company_id,
                Company.tenant_id
                == tenant_id,
            )
            .first()
        )

        if company_exists is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Company not found "
                    "inside current tenant"
                ),
            )

        branch_exists = (
            db.query(Branch.id)
            .filter(
                Branch.id == branch_id,
                Branch.company_id
                == company_id,
                Branch.tenant_id
                == tenant_id,
            )
            .first()
        )

        if branch_exists is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Branch not found "
                    "inside selected company"
                ),
            )

    @staticmethod
    def _raise_not_found() -> None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Transaction not found",
        )

    @staticmethod
    def _raise_invalid_transition(
        current_status: str,
        target_status: str,
    ) -> None:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                f"Cannot change transaction "
                f"from {current_status} "
                f"to {target_status}"
            ),
        )


transaction_service = TransactionService()