import calendar
from datetime import (
    date,
    datetime,
    timezone,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.accounting.fiscal_years.models import (
    AccountingPeriod,
    FiscalYear,
)
from app.modules.accounting.fiscal_years.repositories.fiscal_year_repository import (
    fiscal_year_repository,
)
from app.modules.accounting.fiscal_years.schemas import (
    AccountingPeriodCreate,
    FiscalYearCreate,
    FiscalYearUpdate,
)
from app.modules.companies.models import Company
from app.modules.company_settings.service import get_company_setting
from app.modules.identity.models import User


class FiscalYearService:
    def create_fiscal_year(
        self,
        db: Session,
        payload: FiscalYearCreate,
        current_user: User,
    ) -> FiscalYear:
        tenant_id = self._tenant_id(
            current_user
        )

        self._validate_company(
            db=db,
            tenant_id=tenant_id,
            company_id=payload.company_id,
        )
        required_start_month = int(get_company_setting(db, payload.company_id, "accounting.fiscal_year_start_month"))
        if payload.start_date.month != required_start_month:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Fiscal year must start in company policy month {required_start_month}",
            )

        overlap = (
            fiscal_year_repository
            .find_overlapping_year(
                db=db,
                tenant_id=tenant_id,
                company_id=payload.company_id,
                start_date=payload.start_date,
                end_date=payload.end_date,
            )
        )

        if overlap is not None:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Fiscal year dates overlap "
                    "with an existing fiscal year"
                ),
            )

        fiscal_year = FiscalYear(
            tenant_id=tenant_id,
            company_id=payload.company_id,
            code=payload.code.strip().upper(),
            name_ar=payload.name_ar.strip(),
            name_en=payload.name_en.strip(),
            start_date=payload.start_date,
            end_date=payload.end_date,
            status="draft",
            is_current=False,
            is_adjustment_period_enabled=(
                payload.adjustment_period
            ),
            created_by=current_user.id,
            updated_by=current_user.id,
        )

        db.add(fiscal_year)
        db.flush()

        if payload.create_monthly_periods:
            self._create_monthly_periods(
                db=db,
                fiscal_year=fiscal_year,
                user_id=current_user.id,
            )

        if payload.adjustment_period:
            self._create_adjustment_period(
                db=db,
                fiscal_year=fiscal_year,
                user_id=current_user.id,
            )

        try:
            db.commit()
            db.refresh(fiscal_year)

            return self.get_fiscal_year(
                db=db,
                fiscal_year_id=fiscal_year.id,
                current_user=current_user,
            )

        except IntegrityError as exc:
            db.rollback()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Fiscal year code or period "
                    "already exists"
                ),
            ) from exc

    def get_fiscal_year(
        self,
        db: Session,
        fiscal_year_id: int,
        current_user: User,
    ) -> FiscalYear:
        fiscal_year = (
            fiscal_year_repository.get_by_id(
                db=db,
                fiscal_year_id=fiscal_year_id,
                tenant_id=self._tenant_id(
                    current_user
                ),
            )
        )

        if fiscal_year is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Fiscal year not found",
            )

        return fiscal_year

    def list_fiscal_years(
        self,
        db: Session,
        company_id: int,
        current_user: User,
    ) -> list[FiscalYear]:
        tenant_id = self._tenant_id(
            current_user
        )

        self._validate_company(
            db=db,
            tenant_id=tenant_id,
            company_id=company_id,
        )

        return (
            fiscal_year_repository
            .list_by_company(
                db=db,
                tenant_id=tenant_id,
                company_id=company_id,
            )
        )

    def update_fiscal_year(
        self,
        db: Session,
        fiscal_year_id: int,
        payload: FiscalYearUpdate,
        current_user: User,
    ) -> FiscalYear:
        fiscal_year = self._get_locked(
            db=db,
            fiscal_year_id=fiscal_year_id,
            current_user=current_user,
        )

        if fiscal_year.status != "draft":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only draft fiscal years "
                    "can be edited"
                ),
            )

        update_data = payload.model_dump(
            exclude_unset=True
        )

        new_start_date = update_data.get(
            "start_date",
            fiscal_year.start_date,
        )

        new_end_date = update_data.get(
            "end_date",
            fiscal_year.end_date,
        )

        if new_end_date < new_start_date:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail="Invalid fiscal year dates",
            )

        overlap = (
            fiscal_year_repository
            .find_overlapping_year(
                db=db,
                tenant_id=fiscal_year.tenant_id,
                company_id=fiscal_year.company_id,
                start_date=new_start_date,
                end_date=new_end_date,
                exclude_id=fiscal_year.id,
            )
        )

        if overlap is not None:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Fiscal year dates overlap "
                    "with another fiscal year"
                ),
            )

        for field_name, value in (
            update_data.items()
        ):
            if field_name == "code":
                value = value.strip().upper()

            setattr(
                fiscal_year,
                field_name,
                value,
            )

        fiscal_year.updated_by = (
            current_user.id
        )

        db.commit()
        db.refresh(fiscal_year)

        return self.get_fiscal_year(
            db=db,
            fiscal_year_id=fiscal_year.id,
            current_user=current_user,
        )

    def add_period(
        self,
        db: Session,
        fiscal_year_id: int,
        payload: AccountingPeriodCreate,
        current_user: User,
    ) -> FiscalYear:
        fiscal_year = self._get_locked(
            db=db,
            fiscal_year_id=fiscal_year_id,
            current_user=current_user,
        )

        if fiscal_year.status == "closed":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Cannot add periods to "
                    "a closed fiscal year"
                ),
            )

        if (
            payload.start_date
            < fiscal_year.start_date
            or payload.end_date
            > fiscal_year.end_date
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Accounting period must be "
                    "inside fiscal year dates"
                ),
            )

        for existing_period in (
            fiscal_year.periods
        ):
            overlaps = (
                existing_period.start_date
                <= payload.end_date
                and existing_period.end_date
                >= payload.start_date
            )

            if overlaps:
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Accounting period overlaps "
                        "with an existing period"
                    ),
                )

        period = AccountingPeriod(
            tenant_id=fiscal_year.tenant_id,
            company_id=fiscal_year.company_id,
            fiscal_year_id=fiscal_year.id,
            period_number=payload.period_number,
            code=payload.code.strip().upper(),
            name_ar=payload.name_ar.strip(),
            name_en=payload.name_en.strip(),
            start_date=payload.start_date,
            end_date=payload.end_date,
            status="draft",
            is_adjustment=payload.is_adjustment,
            allow_posting=False,
            created_by=current_user.id,
            updated_by=current_user.id,
        )

        db.add(period)
        db.commit()

        return self.get_fiscal_year(
            db=db,
            fiscal_year_id=fiscal_year.id,
            current_user=current_user,
        )

    def open_fiscal_year(
        self,
        db: Session,
        fiscal_year_id: int,
        current_user: User,
    ) -> FiscalYear:
        fiscal_year = self._get_locked(
            db=db,
            fiscal_year_id=fiscal_year_id,
            current_user=current_user,
        )

        if fiscal_year.status != "draft":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only draft fiscal years "
                    "can be opened"
                ),
            )

        if not fiscal_year.periods:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Fiscal year must contain "
                    "at least one period"
                ),
            )

        now = datetime.now(timezone.utc)

        fiscal_year.status = "open"
        fiscal_year.is_current = True
        fiscal_year.opened_by = current_user.id
        fiscal_year.opened_at = now

        (
            db.query(FiscalYear)
            .filter(
                FiscalYear.tenant_id
                == fiscal_year.tenant_id,
                FiscalYear.company_id
                == fiscal_year.company_id,
                FiscalYear.id
                != fiscal_year.id,
            )
            .update(
                {
                    FiscalYear.is_current: False
                },
                synchronize_session=False,
            )
        )

        for period in fiscal_year.periods:
            if not period.is_adjustment:
                period.status = "open"
                period.allow_posting = True
                period.opened_by = current_user.id
                period.opened_at = now

        db.commit()

        return self.get_fiscal_year(
            db=db,
            fiscal_year_id=fiscal_year.id,
            current_user=current_user,
        )

    def close_period(
        self,
        db: Session,
        period_id: int,
        current_user: User,
    ) -> AccountingPeriod:
        period = (
            fiscal_year_repository
            .get_period_by_id(
                db=db,
                period_id=period_id,
                tenant_id=self._tenant_id(
                    current_user
                ),
                for_update=True,
            )
        )

        if period is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Accounting period not found",
            )

        if period.status != "open":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only open periods "
                    "can be closed"
                ),
            )

        period.status = "closed"
        period.allow_posting = False
        period.closed_by = current_user.id
        period.closed_at = (
            datetime.now(timezone.utc)
        )

        db.commit()
        db.refresh(period)

        return period

    def reopen_period(
        self,
        db: Session,
        period_id: int,
        current_user: User,
    ) -> AccountingPeriod:
        period = (
            fiscal_year_repository
            .get_period_by_id(
                db=db,
                period_id=period_id,
                tenant_id=self._tenant_id(
                    current_user
                ),
                for_update=True,
            )
        )

        if period is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Accounting period not found",
            )

        fiscal_year = (
            fiscal_year_repository.get_by_id(
                db=db,
                fiscal_year_id=(
                    period.fiscal_year_id
                ),
                tenant_id=period.tenant_id,
            )
        )

        if fiscal_year.status != "open":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Fiscal year must be open "
                    "before reopening a period"
                ),
            )

        if period.status not in {
            "closed",
            "closing",
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only closed periods "
                    "can be reopened"
                ),
            )

        period.status = "open"
        period.allow_posting = True
        period.closed_by = None
        period.closed_at = None

        db.commit()
        db.refresh(period)

        return period

    def close_fiscal_year(
        self,
        db: Session,
        fiscal_year_id: int,
        current_user: User,
    ) -> FiscalYear:
        fiscal_year = self._get_locked(
            db=db,
            fiscal_year_id=fiscal_year_id,
            current_user=current_user,
        )

        if fiscal_year.status != "open":
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Only open fiscal years "
                    "can be closed"
                ),
            )

        open_periods = [
            period
            for period in fiscal_year.periods
            if (
                period.status == "open"
                and not period.is_adjustment
            )
        ]

        if open_periods:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "All normal accounting periods "
                    "must be closed first"
                ),
            )

        now = datetime.now(timezone.utc)

        fiscal_year.status = "closed"
        fiscal_year.is_current = False
        fiscal_year.closed_by = current_user.id
        fiscal_year.closed_at = now

        for period in fiscal_year.periods:
            period.status = "locked"
            period.allow_posting = False

        db.commit()

        return self.get_fiscal_year(
            db=db,
            fiscal_year_id=fiscal_year.id,
            current_user=current_user,
        )

    def get_open_period_for_date(
        self,
        db: Session,
        company_id: int,
        posting_date: date,
        current_user: User,
    ) -> AccountingPeriod:
        period = (
            fiscal_year_repository
            .get_period_for_date(
                db=db,
                tenant_id=self._tenant_id(
                    current_user
                ),
                company_id=company_id,
                posting_date=posting_date,
            )
        )

        if period is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "No open accounting period "
                    "exists for the posting date"
                ),
            )

        return period

    @staticmethod
    def _create_monthly_periods(
        db: Session,
        fiscal_year: FiscalYear,
        user_id: int,
    ) -> None:
        period_start = fiscal_year.start_date

        period_number = 1

        while period_start <= fiscal_year.end_date:
            last_day = calendar.monthrange(
                period_start.year,
                period_start.month,
            )[1]

            natural_month_end = date(
                period_start.year,
                period_start.month,
                last_day,
            )

            period_end = min(
                natural_month_end,
                fiscal_year.end_date,
            )

            period = AccountingPeriod(
                tenant_id=fiscal_year.tenant_id,
                company_id=fiscal_year.company_id,
                fiscal_year_id=fiscal_year.id,
                period_number=period_number,
                code=(
                    f"{fiscal_year.code}-"
                    f"{period_number:02d}"
                ),
                name_ar=(
                    f"الفترة {period_number:02d}"
                ),
                name_en=(
                    f"Period {period_number:02d}"
                ),
                start_date=period_start,
                end_date=period_end,
                status="draft",
                is_adjustment=False,
                allow_posting=False,
                created_by=user_id,
                updated_by=user_id,
            )

            db.add(period)

            period_number += 1

            if period_end >= fiscal_year.end_date:
                break

            next_month = (
                period_end.month + 1
            )

            next_year = period_end.year

            if next_month == 13:
                next_month = 1
                next_year += 1

            period_start = date(
                next_year,
                next_month,
                1,
            )

    @staticmethod
    def _create_adjustment_period(
        db: Session,
        fiscal_year: FiscalYear,
        user_id: int,
    ) -> None:
        period_number = (
            len(
                [
                    period
                    for period in fiscal_year.periods
                    if not period.is_adjustment
                ]
            )
            + 1
        )

        period = AccountingPeriod(
            tenant_id=fiscal_year.tenant_id,
            company_id=fiscal_year.company_id,
            fiscal_year_id=fiscal_year.id,
            period_number=period_number,
            code=(
                f"{fiscal_year.code}-ADJ"
            ),
            name_ar="فترة التسويات",
            name_en="Adjustment Period",
            start_date=fiscal_year.end_date,
            end_date=fiscal_year.end_date,
            status="draft",
            is_adjustment=True,
            allow_posting=False,
            created_by=user_id,
            updated_by=user_id,
        )

        db.add(period)

    def _get_locked(
        self,
        db: Session,
        fiscal_year_id: int,
        current_user: User,
    ) -> FiscalYear:
        fiscal_year = (
            fiscal_year_repository.get_by_id(
                db=db,
                fiscal_year_id=fiscal_year_id,
                tenant_id=self._tenant_id(
                    current_user
                ),
                for_update=True,
            )
        )

        if fiscal_year is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Fiscal year not found",
            )

        return fiscal_year

    @staticmethod
    def _tenant_id(
        current_user: User,
    ) -> int:
        if current_user.is_platform_admin:
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Platform administrator "
                    "has no tenant context"
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
    def _validate_company(
        db: Session,
        tenant_id: int,
        company_id: int,
    ) -> None:
        company = (
            db.query(Company.id)
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


fiscal_year_service = FiscalYearService()