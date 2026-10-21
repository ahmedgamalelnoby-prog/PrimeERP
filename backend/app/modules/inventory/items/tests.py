from decimal import Decimal

from app.modules.inventory.items.schemas import InventoryItemCreate, InventoryItemUpdate


def test_inventory_item_create_defaults():
    item = InventoryItemCreate(company_id=1, sku="SKU-001", name_ar="صنف")
    assert item.item_type == "stockable"
    assert item.costing_method == "weighted_average"
    assert item.standard_cost == Decimal("0")


def test_inventory_item_update_is_partial():
    payload = InventoryItemUpdate(sales_price=Decimal("125.50"))
    assert payload.model_dump(exclude_unset=True) == {"sales_price": Decimal("125.50")}
