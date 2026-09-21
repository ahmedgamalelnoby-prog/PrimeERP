from pathlib import Path


def test_reservation_variant_migration_matches_model():
    migration = Path(__file__).resolve().parents[2] / "alembic" / "versions" / "20260921_reservation_variant_alignment.py"
    text = migration.read_text(encoding="utf-8")
    assert 'sa.Column("variant_id", sa.Integer(), nullable=True)' in text
    assert '"fk_inventory_reservations_variant_id"' in text
    assert '"ix_inventory_reservations_variant_id"' in text
