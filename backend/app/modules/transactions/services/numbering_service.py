from datetime import (
    datetime,
    timezone,
)
from typing import Optional

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.branches.models import Branch
from app.modules.companies.models import Company
from app.modules.transactions.models import (
    NumberSequence,
)
from app.modules.transactions.repositories.number_sequence_repository import (
    number_sequence_repository,
)
from app.modules.transactions.schemas.number_sequence import (
    NumberSequenceCreate,
    NumberSequenceUpdate,
)


class NumberingService:
    def create_sequence(
        self,
        db: Session,
        payload: NumberSequenceCreate,
        current_tenant_id: int,
    ) -> NumberSequence:
        self._validate_tenant_access(
            requested_tenant_id=(
                payload.tenant_id
            ),
            current_tenant_id=(
                current_tenant_id
            ),
        )

        company, branch = (
            self._validate_organization_scope(
                db=db,
                tenant_id=payload.tenant_id,
                company_id=payload.company_id,
                branch_id=payload.branch_id,
            )
        )

        existing = (
            number_sequence_repository
            .get_by_scope(
                db=db,
                tenant_id=payload.tenant_id,
                company_id=payload.company_id,
                branch_id=payload.branch_id,
                sequence_key=(
                    payload.sequence_key
                ),
            )
        )

        if existing is not None:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "A numbering sequence already "
                    "exists for this scope"
                ),
            )

        sequence = NumberSequence(
            tenant_id=payload.tenant_id,
            company_id=payload.company_id,
            branch_id=payload.branch_id,
            sequence_key=(
                payload.sequence_key
            ),
            prefix=payload.prefix,
            format_pattern=(
                payload.format_pattern
            ),
            current_value=(
                payload.current_value
            ),
            padding=payload.padding,
            reset_period=(
                payload.reset_period
            ),
            last_reset_year=None,
            last_reset_month=None,
            is_active=payload.is_active,
        )

        try:
            number_sequence_repository.add(
                db=db,
                sequence=sequence,
            )

            db.commit()
            db.refresh(sequence)

            return sequence

        except IntegrityError as exc:
            db.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Numbering sequence already exists"
                ),
            ) from exc

    def update_sequence(
        self,
        db: Session,
        sequence_id: int,
        payload: NumberSequenceUpdate,
        current_tenant_id: int,
    ) -> NumberSequence:
        sequence = self.get_sequence(
            db=db,
            sequence_id=sequence_id,
            current_tenant_id=(
                current_tenant_id
            ),
        )

        update_data = payload.model_dump(
            exclude_unset=True
        )

        for field_name, value in (
            update_data.items()
        ):
            setattr(
                sequence,
                field_name,
                value,
            )

        db.commit()
        db.refresh(sequence)

        return sequence

    def get_sequence(
        self,
        db: Session,
        sequence_id: int,
        current_tenant_id: int,
    ) -> NumberSequence:
        sequence = (
            number_sequence_repository
            .get_by_id(
                db=db,
                sequence_id=sequence_id,
            )
        )

        if sequence is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Numbering sequence not found"
                ),
            )

        self._validate_tenant_access(
            requested_tenant_id=(
                sequence.tenant_id
            ),
            current_tenant_id=(
                current_tenant_id
            ),
        )

        return sequence

    def list_sequences(
        self,
        db: Session,
        current_tenant_id: int,
        company_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> list[NumberSequence]:
        return (
            number_sequence_repository
            .list_by_tenant(
                db=db,
                tenant_id=current_tenant_id,
                company_id=company_id,
                branch_id=branch_id,
                is_active=is_active,
            )
        )

    def generate_next_number(
        self,
        db: Session,
        tenant_id: int,
        company_id: int,
        branch_id: int,
        sequence_key: str,
        commit: bool = True,
    ) -> dict:
        """
        Generates the next number safely.

        PostgreSQL SELECT FOR UPDATE locks the sequence
        row until the transaction is committed, preventing
        two requests from receiving the same number.
        """

        normalized_key = (
            sequence_key.strip().upper()
        )

        company, branch = (
            self._validate_organization_scope(
                db=db,
                tenant_id=tenant_id,
                company_id=company_id,
                branch_id=branch_id,
            )
        )

        try:
            sequence = (
                number_sequence_repository
                .get_by_scope(
                    db=db,
                    tenant_id=tenant_id,
                    company_id=company_id,
                    branch_id=branch_id,
                    sequence_key=normalized_key,
                    for_update=True,
                )
            )

            if sequence is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail=(
                        "Numbering sequence is "
                        "not configured"
                    ),
                )

            if not sequence.is_active:
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Numbering sequence is inactive"
                    ),
                )

            now = datetime.now(timezone.utc)

            self._apply_period_reset(
                sequence=sequence,
                now=now,
            )

            sequence.current_value += 1

            formatted_number = (
                self._format_number(
                    sequence=sequence,
                    company_code=(
                        company.code or "COMP"
                    ),
                    branch_code=(
                        branch.code or "BR"
                    ),
                    now=now,
                )
            )

            db.flush()

            if commit:
               db.commit()
               db.refresh(sequence)

            return {
                "sequence_id": sequence.id,
                "sequence_key": (
                    sequence.sequence_key
                ),
                "generated_number": (
                    formatted_number
                ),
                "sequence_value": (
                    sequence.current_value
                ),
                "generated_at": now,
            }

        except HTTPException:
             if commit:
                 db.rollback()
             raise

        except Exception as exc:
            if commit:
              db.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "Could not generate "
                    "the next number"
                ),
            ) from exc

    @staticmethod
    def _apply_period_reset(
        sequence: NumberSequence,
        now: datetime,
    ) -> None:
        if sequence.reset_period == "never":
            return

        if sequence.reset_period == "yearly":
            if (
                sequence.last_reset_year
                != now.year
            ):
                sequence.current_value = 0
                sequence.last_reset_year = (
                    now.year
                )
                sequence.last_reset_month = (
                    now.month
                )

            return

        if sequence.reset_period == "monthly":
            if (
                sequence.last_reset_year
                != now.year
                or sequence.last_reset_month
                != now.month
            ):
                sequence.current_value = 0
                sequence.last_reset_year = (
                    now.year
                )
                sequence.last_reset_month = (
                    now.month
                )

    @staticmethod
    def _format_number(
        sequence: NumberSequence,
        company_code: str,
        branch_code: str,
        now: datetime,
    ) -> str:
        padded_sequence = str(
            sequence.current_value
        ).zfill(sequence.padding)

        tokens = {
            "{PREFIX}": sequence.prefix,
            "{YEAR}": str(now.year),
            "{YY}": str(now.year)[-2:],
            "{MONTH}": str(
                now.month
            ).zfill(2),
            "{COMPANY}": (
                company_code.strip().upper()
            ),
            "{BRANCH}": (
                branch_code.strip().upper()
            ),
            "{SEQ}": padded_sequence,
        }

        generated_number = (
            sequence.format_pattern
        )

        for token, token_value in (
            tokens.items()
        ):
            generated_number = (
                generated_number.replace(
                    token,
                    token_value,
                )
            )

        return generated_number

    @staticmethod
    def _validate_organization_scope(
        db: Session,
        tenant_id: int,
        company_id: int,
        branch_id: int,
    ) -> tuple[Company, Branch]:
        company = (
            db.query(Company)
            .filter(
                Company.id == company_id,
                Company.tenant_id
                == tenant_id,
            )
            .first()
        )

        if company is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Company not found "
                    "inside current tenant"
                ),
            )

        branch = (
            db.query(Branch)
            .filter(
                Branch.id == branch_id,
                Branch.company_id
                == company_id,
                Branch.tenant_id
                == tenant_id,
            )
            .first()
        )

        if branch is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Branch not found "
                    "inside selected company"
                ),
            )

        return company, branch

    @staticmethod
    def _validate_tenant_access(
        requested_tenant_id: int,
        current_tenant_id: int,
    ) -> None:
        if (
            requested_tenant_id
            != current_tenant_id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Access to another tenant "
                    "is not allowed"
                ),
            )


numbering_service = NumberingService()