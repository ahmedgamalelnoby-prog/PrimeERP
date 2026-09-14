from app.modules.inventory.adjustments.models import InventoryAdjustment
from app.modules.inventory.items.models import InventoryStock
from app.modules.inventory.reservations.models import InventoryReservation
from app.modules.inventory.stock_moves.location_stock import InventoryLocationStock
from app.modules.inventory.stock_moves.models import InventoryCostLayer, InventoryStockMove
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.reservations.schemas import ReservationCreate


def test_variant_dimension_exists_across_inventory_ledgers():
    for model in (InventoryStock, InventoryLocationStock, InventoryStockMove, InventoryCostLayer, InventoryReservation, InventoryAdjustment):
        assert "variant_id" in model.__table__.c


def test_variant_is_optional_for_legacy_parent_product_stock():
    for model in (InventoryStock, InventoryLocationStock, InventoryStockMove, InventoryCostLayer, InventoryReservation, InventoryAdjustment):
        assert model.__table__.c.variant_id.nullable is True


def test_stock_move_and_reservation_contract_expose_variant():
    assert "variant_id" in StockMoveCreate.model_fields
    assert "variant_id" in ReservationCreate.model_fields


def test_stock_move_has_variant_foreign_key():
    foreign_keys = {fk.target_fullname for fk in InventoryStockMove.__table__.c.variant_id.foreign_keys}
    assert "product_variants.id" in foreign_keys
