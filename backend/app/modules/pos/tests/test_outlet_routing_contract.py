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
