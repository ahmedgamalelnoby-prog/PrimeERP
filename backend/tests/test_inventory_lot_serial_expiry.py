from datetime import date
from decimal import Decimal

from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.items.schemas import InventoryItemCreate, InventoryItemResponse
from app.modules.inventory.stock_moves.models import InventoryStockMove
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