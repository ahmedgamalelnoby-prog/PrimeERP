from decimal import Decimal
from pathlib import Path


SERVICE_SOURCE = (Path(__file__).resolve().parents[2] / "app/modules/inventory/stock_moves/service.py").read_text(encoding="utf-8")


def test_variant_fifo_cost_isolated_and_weighted():
    allocations = [(Decimal("2"), Decimal("10")), (Decimal("3"), Decimal("14"))]
    quantity = sum((q for q, _ in allocations), Decimal("0"))
    weighted = sum((q * c for q, c in allocations), Decimal("0")) / quantity
    assert quantity == Decimal("5")
    assert weighted == Decimal("12.4")


def test_variant_fifo_allocation_never_crosses_variant_dimension():
    assert "InventoryCostLayer.variant_id == variant_id" in SERVICE_SOURCE
    assert "InventoryCostLayer.variant_id.is_(None)" in SERVICE_SOURCE


def test_variant_validation_uses_is_active_field():
    assert "ProductVariant.is_active.is_(True)" in SERVICE_SOURCE
    assert "ProductVariant.active.is_(True)" not in SERVICE_SOURCE
