from typing import Optional

from sqlalchemy.orm import Session

from app.modules.platform.plans.exceptions import (
    ArchivedPlanModificationError,
    DefaultPlanAlreadyExistsError,
    PlanCodeAlreadyExistsError,
    PlanNotFoundError,
    PlanValidationError,
)
from app.modules.platform.plans.models import Plan
from app.modules.platform.plans.repository import PlanRepository
from app.modules.platform.plans.schemas import (
    PlanCreate,
    PlanUpdate,
)
from app.modules.saas.models import Subscription


class PlanService:

    # Once a plan has ever been assigned to a subscription, its commercial
    # contract must remain immutable. Otherwise changing price/limits/trial
    # values on the same plan row silently changes historical and active
    # subscriptions because subscriptions reference the legacy plan id.
    _CATALOG_ONLY_FIELDS = frozenset({
        "is_default",
        "is_public",
        "status",
        "sort_order",
    })

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = PlanRepository()

    def get_plan(
        self,
        plan_id: int,
    ) -> Plan:
        plan = self.repository.get_by_id(
            db=self.db,
            plan_id=plan_id,
        )

        if plan is None:
            raise PlanNotFoundError(plan_id)

        return plan

    def get_plan_by_code(
        self,
        code: str,
        version: int = 1,
    ) -> Plan:
        plan = self.repository.get_by_code(
            db=self.db,
            code=code,
            version=version,
        )

        if plan is None:
            raise PlanNotFoundError(code)

        return plan

    def get_default_plan(self) -> Optional[Plan]:
        return self.repository.get_default(
            db=self.db,
        )

    def get_all_plans(self) -> list[Plan]:
        return self.repository.get_all(
            db=self.db,
        )

    def create_plan(
        self,
        schema: PlanCreate,
    ) -> Plan:
        code = schema.code.strip().lower()

        existing_plan = self.repository.get_by_code(
            db=self.db,
            code=code,
            version=1,
        )

        if existing_plan is not None:
            raise PlanCodeAlreadyExistsError(code)

        if schema.is_default:
            default_plan = self.repository.get_default(
                db=self.db,
            )

            if default_plan is not None:
                raise DefaultPlanAlreadyExistsError()

        data = schema.model_dump(
            mode="json",
        )

        data["code"] = code
        data["version"] = 1

        plan = self.repository.create(
            db=self.db,
            data=data,
        )

        self.db.commit()
        self.repository.refresh(
            db=self.db,
            instance=plan,
        )

        return plan

    def _has_subscription_history(self, plan_id: int) -> bool:
        """Return True when this plan id has ever been assigned to a tenant."""
        return (
            self.db.query(Subscription)
            .filter(Subscription.plan_id == plan_id)
            .first()
            is not None
        )

    def _validate_referenced_plan_update(self, plan: Plan, data: dict) -> None:
        if not data or not self._has_subscription_history(plan.id):
            return

        changed_contract_fields = set(data) - self._CATALOG_ONLY_FIELDS
        if changed_contract_fields:
            fields = ", ".join(sorted(changed_contract_fields))
            raise PlanValidationError(
                "A plan that has been assigned to a subscription is immutable. "
                "Create a new plan/version for commercial changes. "
                f"Restricted fields: {fields}."
            )

    def update_plan(
        self,
        plan_id: int,
        schema: PlanUpdate,
    ) -> Plan:
        plan = self.repository.get_by_id(
            db=self.db,
            plan_id=plan_id,
            for_update=True,
        )

        if plan is None:
            raise PlanNotFoundError(plan_id)

        data = schema.model_dump(
            exclude_unset=True,
            mode="json",
        )

        self._validate_referenced_plan_update(plan, data)

        if "code" in data and data["code"] is not None:
            data["code"] = data["code"].strip().lower()

            existing_plan = self.repository.get_by_code(
                db=self.db,
                code=data["code"],
                version=plan.version,
            )

            if (
                existing_plan is not None
                and existing_plan.id != plan.id
            ):
                raise PlanCodeAlreadyExistsError(data["code"])

        if data.get("is_default") is True:
            default_plan = self.repository.get_default(
                db=self.db,
            )

            if (
                default_plan is not None
                and default_plan.id != plan.id
            ):
                raise DefaultPlanAlreadyExistsError()

        plan = self.repository.update(
            db=self.db,
            instance=plan,
            data=data,
        )

        self.db.commit()
        self.repository.refresh(
            db=self.db,
            instance=plan,
        )

        return plan

    def delete_plan(
        self,
        plan_id: int,
    ) -> None:
        plan = self.repository.get_by_id(
            db=self.db,
            plan_id=plan_id,
            for_update=True,
        )

        if plan is None:
            raise PlanNotFoundError(plan_id)

        if self._has_subscription_history(plan.id):
            raise ArchivedPlanModificationError()

        self.repository.soft_delete(
            db=self.db,
            instance=plan,
        )

        self.db.commit()
