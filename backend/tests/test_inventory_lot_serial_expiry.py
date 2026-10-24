from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.items.schemas import InventoryItemCreate, InventoryItemResponse, InventoryItemUpdate
from app.modules.inventory.stock_moves.models import InventoryLotBalance, InventoryLotMoveAllocation, InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate


def test_inventory_item_exposes_tracking_defaults_and_response_fields():
    for name in ("batch_tracking", "serial_tracking", "expiry_tracking"):
        assert name in InventoryItem.__table__.c
        assert name in InventoryItemCreate.model_fields
        assert name in InventoryItemResponse.model_fields


def test_stock_move_persists_lot_serial_and_expiry_identity():
    for name in ("lot_number", "serial_number", "expiry_date"):
        assert name in InventoryStockMove.__table__.c
        assert name in StockMoveCreate.model_fields

    move = StockMoveCreate(
        company_id=7,
        item_id=11,
        quantity=Decimal("1"),
        movement_type="receipt",
        destination_location_id=5,
        lot_number="LOT-2026-01",
        serial_number="SER-0001",
        expiry_date=date(2027, 1, 31),
    )
    assert move.lot_number == "LOT-2026-01"
    assert move.serial_number == "SER-0001"
    assert move.expiry_date == date(2027, 1, 31)


@pytest.mark.parametrize("field", ["batch_tracking", "serial_tracking", "expiry_tracking"])
def test_inventory_item_update_rejects_null_tracking_flags(field):
    with pytest.raises(ValidationError):
        InventoryItemUpdate.model_validate({field: None})


def test_inventory_item_update_accepts_explicit_tracking_boolean():
    update = InventoryItemUpdate.model_validate({"batch_tracking": False})
    assert update.batch_tracking is False


def test_lot_balances_and_movement_allocations_have_auditable_identity():
    assert {"company_id", "item_id", "variant_id", "location_id", "lot_number", "serial_number", "expiry_date", "quantity_on_hand"} <= set(InventoryLotBalance.__table__.c.keys())
    assert {"company_id", "stock_move_id", "lot_number", "serial_number", "expiry_date", "quantity"} <= set(InventoryLotMoveAllocation.__table__.c.keys())
    assert "uq_inventory_lot_balance_identity" in {index.name for index in InventoryLotBalance.__table__.indexes}
