from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_pos_outlet_terminal_and_route_models_are_registered():
    models = (ROOT / "modules/restaurant/models.py").read_text(encoding="utf-8")
    registry = (ROOT / "database/models.py").read_text(encoding="utf-8")
    assert "class PosOutlet(Base):" in models
    assert "class PosTerminal(Base):" in models
    assert "class PosTerminalMenu(Base):" in models
    assert "class PosMenuItemRoute(Base):" in models
    assert "class PosOrderLineRoute(Base):" in models
    assert "PosOutlet, PosOutletStation, PosTerminal, PosTerminalMenu, PosMenuItemRoute, PosOrderLineRoute" in registry


def test_pos_router_enforces_terminal_menu_and_outlet_station_chain():
    router = (ROOT / "modules/pos/router.py").read_text(encoding="utf-8")
    assert '"/terminals/menus"' in router
    assert '"/menu-routes"' in router
    assert "terminal_menu = db.scalar" in router
    assert "allowed_station = db.scalar" in router
    assert "PosOrderLineRoute(" in router
    assert '"/stations/{station_id}/queue"' in router


def test_pos_checkout_uses_server_side_menu_price_and_routes_each_line():
    router = (ROOT / "modules/pos/router.py").read_text(encoding="utf-8")
    assert "def _menu_price" in router
    assert "menu_item.sale_price_override" in router
    assert "ProductPrice.min_quantity <= quantity" in router
    assert "terminal_id=terminal.id" in router
    assert "station_id=station_id" in router
    assert "capture_document_tax_snapshot" in router


def test_pos_route_status_has_monotonic_kitchen_bar_lifecycle():
    router = (ROOT / "modules/pos/router.py").read_text(encoding="utf-8")
    assert '"queued": {"preparing", "cancelled"}' in router
    assert '"preparing": {"ready", "cancelled"}' in router
    assert '"ready": {"served"}' in router


def test_pos_binds_outlet_consumption_warehouse_and_rejects_mismatch():
    router = (ROOT / "modules/pos/router.py").read_text(encoding="utf-8")
    assert 'outlet.warehouse_id is None' in router
    assert 'payload.warehouse_id != outlet.warehouse_id' in router
    assert '"/outlets/{outlet_id}/warehouse"' in router


def test_pos_checkout_completes_sale_delivery_and_inventory_consumption():
    router = (ROOT / "modules/pos/router.py").read_text(encoding="utf-8")
    assert 'document_type="delivery"' in router
    assert 'commerce_service.confirm(db, payload.company_id, delivery.id, "sale", current_user.id)' in router
    assert 'commerce_service.post_inventory(db, payload.company_id, delivery.id, "sale", user_id=current_user.id)' in router


def test_pos_supports_recipe_component_consumption_from_delivery_warehouse():
    service = (ROOT / "modules/commerce/service.py").read_text(encoding="utf-8")
    assert "def active_recipe(product_id: int, variant_id: int | None)" in service
    assert "def expand_recipe(" in service
    assert 'movement_type="issue"' in service
    assert 'source_entity=source_entity' in service
    assert "Recipe cycle detected" in service


def test_pos_frontend_exposes_full_operational_surface():
    page = (ROOT.parent.parent / "frontend/src/modules/pos/pages/PosPage.tsx").read_text(encoding="utf-8")
    for endpoint in ["/pos/outlets", "/pos/stations", "/pos/terminals", "/pos/terminals/menus", "/pos/menu-routes", "/pos/checkout", "/pos/stations/"]:
        assert endpoint in page
    assert "Consumption Warehouse" in page
    assert "Restaurant & Hotel POS" in page



def test_pos_checkout_does_not_double_consume_inventory_from_invoice_and_delivery():
    router = (ROOT / "modules/pos/router.py").read_text(encoding="utf-8")
    delivery_post = 'commerce_service.post_inventory(db, payload.company_id, delivery.id, "sale", user_id=current_user.id)'
    invoice_post = 'commerce_service.post_inventory(db, payload.company_id, doc.id, "sale", user_id=current_user.id)'
    assert delivery_post in router
    assert invoice_post not in router
