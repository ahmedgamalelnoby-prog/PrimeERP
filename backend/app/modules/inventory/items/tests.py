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

def test_inventory_item_create_uses_company_tracking_defaults(monkeypatch):
    from types import SimpleNamespace

    from app.modules.inventory.items.service import InventoryItemService

    service = InventoryItemService()
    monkeypatch.setattr(service, "_validate_category", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(service, "_resolve_uom", lambda *_args, **_kwargs: SimpleNamespace(id=4, code="unit"))
    monkeypatch.setattr(service, "_validate_commercial_uoms", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(service, "_validate_tax_profiles", lambda **_kwargs: ([], []))
    monkeypatch.setattr("app.modules.inventory.items.service.enforce_product_limit", lambda *_args: None)
    monkeypatch.setattr(
        "app.modules.inventory.items.service.get_company_setting",
        lambda _db, _company_id, key: {
            "inventory.batch_tracking_default": True,
            "inventory.serial_tracking_default": False,
            "inventory.expiry_tracking_required": True,
            "inventory.valuation_method": "fifo",
        }[key],
    )

    class FakeDB:
        def add(self, _item):
            pass

        def commit(self):
            pass

        def refresh(self, _item):
            pass

    item = service.create(
        FakeDB(),
        InventoryItemCreate(company_id=7, sku="TRACK-001", name_ar="صنف تتبع"),
    )

    assert item.batch_tracking is True
    assert item.serial_tracking is False
    assert item.expiry_tracking is True
    assert item.costing_method == "fifo"


def test_inventory_item_explicit_tracking_flags_override_company_defaults(monkeypatch):
    from types import SimpleNamespace

    from app.modules.inventory.items.service import InventoryItemService

    service = InventoryItemService()
    monkeypatch.setattr(service, "_validate_category", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(service, "_resolve_uom", lambda *_args, **_kwargs: SimpleNamespace(id=4, code="unit"))
    monkeypatch.setattr(service, "_validate_commercial_uoms", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(service, "_validate_tax_profiles", lambda **_kwargs: ([], []))
    monkeypatch.setattr("app.modules.inventory.items.service.enforce_product_limit", lambda *_args: None)
    monkeypatch.setattr(
        "app.modules.inventory.items.service.get_company_setting",
        lambda _db, _company_id, key: True if key in {
            "inventory.batch_tracking_default",
            "inventory.serial_tracking_default",
            "inventory.expiry_tracking_required",
        } else "fifo",
    )

    class FakeDB:
        def add(self, _item):
            pass

        def commit(self):
            pass

        def refresh(self, _item):
            pass

    item = service.create(
        FakeDB(),
        InventoryItemCreate(
            company_id=7,
            sku="TRACK-002",
            name_ar="صنف يدوي",
            batch_tracking=False,
            serial_tracking=False,
            expiry_tracking=False,
        ),
    )

    assert item.batch_tracking is False
    assert item.serial_tracking is False
    assert item.expiry_tracking is False

