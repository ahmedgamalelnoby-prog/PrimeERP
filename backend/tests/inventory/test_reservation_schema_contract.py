from pathlib import Path


def test_reservation_variant_migration_is_declared_once():
    migration = Path(__file__).resolve().parents[2] / "alembic" / "versions" / "20260914_variant_inventory_dimension.py"
    text = migration.read_text(encoding="utf-8")
    assert '_add_variant("inventory_reservations")' in text
    assert 'fk_{table}_variant_id' in text
    assert 'ix_{table}_variant_id' in text
