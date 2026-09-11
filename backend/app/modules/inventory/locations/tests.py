from app.modules.inventory.locations.models import InventoryLocation


def test_location_table_and_hierarchy_contract():
    assert InventoryLocation.__tablename__ == "inventory_locations"
    assert "parent_id" in InventoryLocation.__table__.c
    assert "warehouse_id" in InventoryLocation.__table__.c
    assert "uq_inventory_location_warehouse_code" in {
        constraint.name for constraint in InventoryLocation.__table__.constraints
    }
