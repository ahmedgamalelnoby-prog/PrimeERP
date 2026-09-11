from decimal import Decimal

from app.modules.inventory.stock_moves.models import InventoryStockMove


def test_stock_move_contract():
    assert InventoryStockMove.__tablename__ == "inventory_stock_moves"
    assert "quantity" in InventoryStockMove.__table__.c
    assert "source_location_id" in InventoryStockMove.__table__.c
    assert "destination_location_id" in InventoryStockMove.__table__.c


def test_stock_move_quantity_is_positive():
    constraint_names = {c.name for c in InventoryStockMove.__table__.constraints}
    assert "ck_inventory_stock_move_quantity" in constraint_names
    assert Decimal("1") > 0
