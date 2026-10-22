from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ApprovalMode = Literal["sequential", "parallel", "any_one"]


class ApprovalRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: int = Field(gt=0)
    entity_type: str = Field(min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9_.:-]+$")
    entity_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=2, max_length=240)
    approver_ids: list[int] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def unique_approvers(self):
        if any(isinstance(i, bool) or i <= 0 for i in self.approver_ids):
            raise ValueError("Approver IDs must be positive integers")
        if len(set(self.approver_ids)) != len(self.approver_ids):
            raise ValueError("Approver IDs must be unique")
        return self


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject"]
    reason: str | None = Field(default=None, max_length=2000)


class ApprovalStepView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    approver_user_id: int
    sequence_no: int
    status: str
    decided_by_user_id: int | None
    reason: str | None
    decided_at: datetime | None


class ApprovalRequestView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    company_id: int
    entity_type: str
    entity_id: int | None
    title: str
    requested_by_user_id: int
    mode: str
    status: str
    created_at: datetime
    decided_at: datetime | None
    steps: list[ApprovalStepView] = []
