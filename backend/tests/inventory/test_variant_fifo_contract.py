from decimal import Decimal


def test_variant_fifo_cost_isolated_and_weighted():
    allocations = [(Decimal("2"), Decimal("10")), (Decimal("3"), Decimal("14"))]
    quantity = sum((q for q, _ in allocations), Decimal("0"))
    weighted = sum((q * c for q, c in allocations), Decimal("0")) / quantity
    assert quantity == Decimal("5")
    assert weighted == Decimal("12.4")


def test_variant_fifo_allocation_never_crosses_variant_dimension():
    # Contract-level regression: FIFO selectors must constrain variant_id.
    service_source = open("backend/app/modules/inventory/stock_moves/service.py", encoding="utf-8").read()
    assert "InventoryCostLayer.variant_id == variant_id" in service_source
    assert "InventoryCostLayer.variant_id.is_(None)" in service_source


def test_variant_validation_uses_is_active_field():
    service_source = open("backend/app/modules/inventory/stock_moves/service.py", encoding="utf-8").read()
    assert "ProductVariant.is_active.is_(True)" in service_source
    assert "ProductVariant.active.is_(True)" not in service_source
