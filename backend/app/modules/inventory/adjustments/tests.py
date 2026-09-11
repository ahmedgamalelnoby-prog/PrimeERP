from decimal import Decimal


def test_adjustment_contract_defaults():
    from app.modules.inventory.adjustments.schemas import AdjustmentCreate

    payload = AdjustmentCreate(
        company_id=1,
        item_id=2,
        location_id=3,
        quantity=Decimal("5"),
        direction="increase",
        reason="Cycle count",
    )
    assert payload.unit_cost == 0
    assert payload.direction == "increase"
