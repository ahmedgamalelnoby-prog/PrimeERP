from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_stage8_pos_e2e_contract_is_explicit():
    service = (ROOT / "app/modules/pos/service.py").read_text()
    router = (ROOT / "app/modules/pos/router.py").read_text()
    schemas = (ROOT / "app/modules/pos/schemas.py").read_text()
    models = (ROOT / "app/modules/pos/models.py").read_text()

    assert "Cashier is inactive, deleted, or outside the current tenant" in service
    assert "Variant does not belong to the item/company or is inactive" in service
    assert "POS accounting journal must have auto-post enabled" in service
    assert "Session closing total" in service
    assert 'method in ("cash","card","bank","other")' in service
    assert "closing_cash" in schemas
    assert "closing_card" in schemas
    assert "closing_bank" in schemas
    assert "closing_other" in schemas
    assert "closing_cash" in models
    assert "closing_other" in models
    assert "p.closing_cash" in router


def test_stage8_reservation_variant_contract_uses_canonical_flag():
    service = (ROOT / "app/modules/inventory/reservations/service.py").read_text()
    assert "ProductVariant.is_active.is_(True)" in service
    assert "ProductVariant.active.is_(True)" not in service


def test_stage8_migration_remains_downstream_of_stage7_financial_hardening():
    migration = (ROOT / "alembic/versions/20260921_pos_financial_hardening.py").read_text()
    assert 'down_revision = "20260921_stage7_domain_merge"' in migration
    assert 'op.add_column("pos_sessions", sa.Column("closing_cash"' in migration
