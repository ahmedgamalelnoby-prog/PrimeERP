from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class WorkOrderCreate(BaseModel):
    company_id: int = Field(gt=0)
    recipe_id: int = Field(gt=0)
    number: str = Field(min_length=1, max_length=60)
    source_location_id: int = Field(gt=0)
    destination_location_id: int = Field(gt=0)
    planned_quantity: Decimal = Field(gt=0)


class WorkOrderComplete(BaseModel):
    produced_quantity: Decimal = Field(gt=0)


class WorkOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_recipe_line_id: int
    ingredient_item_id: int
    quantity_per_output: Decimal
    issued_quantity: Decimal | None
    issue_move_id: int | None


class WorkOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    number: str
    recipe_id: int
    recipe_version: int
    output_item_id: int
    output_variant_id: int | None
    source_location_id: int
    destination_location_id: int
    planned_quantity: Decimal
    produced_quantity: Decimal | None
    status: str
    created_by_user_id: int
    released_by_user_id: int | None
    completed_by_user_id: int | None
    created_at: object
    released_at: object | None
    completed_at: object | None
    lines: list[WorkOrderLineResponse]
