from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


Channel = Literal["email", "whatsapp", "in_app"]


class TemplateUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    channel: Channel
    title_template: str = Field(default="", max_length=255)
    body_template: str = Field(min_length=1, max_length=10000)
    is_active: bool = True


class GroupMemberInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination: str = Field(min_length=3, max_length=320)
    label: str = Field(default="", max_length=160)


class GroupUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    name: str = Field(min_length=1, max_length=160)
    channel: Literal["email", "whatsapp"]
    members: list[GroupMemberInput] = Field(min_length=1, max_length=100)
    is_active: bool = True

    @field_validator("members")
    @classmethod
    def unique_destinations(cls, value):
        normalized = [member.destination.strip().lower() for member in value]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Group destinations must be unique")
        return value


class SendNotificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: int = Field(gt=0)
    channel: Channel
    destination: str | None = Field(default=None, min_length=3, max_length=320)
    group_id: int | None = Field(default=None, gt=0)
    template_code: str | None = Field(default=None, min_length=1, max_length=80)
    title: str = Field(default="", max_length=255)
    body: str = Field(default="", max_length=10000)
    context: dict[str, str | int | float | bool | None] = Field(default_factory=dict, max_length=50)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=120)

    @field_validator("context")
    @classmethod
    def bounded_context(cls, value):
        if any(len(str(k)) > 80 for k in value):
            raise ValueError("Template context keys must be at most 80 characters")
        return value
