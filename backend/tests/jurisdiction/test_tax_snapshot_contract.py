from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = (ROOT / "app/modules/jurisdiction/models.py").read_text(encoding="utf-8")
SERVICE = (ROOT / "app/modules/jurisdiction/snapshot_service.py").read_text(encoding="utf-8")
MIGRATION = (ROOT / "alembic/versions/20260914_tax_snapshots.py").read_text(encoding="utf-8")
GLOBAL_MIGRATION = (ROOT / "alembic/versions/20260914_global_jurisdiction.py").read_text(encoding="utf-8")


def test_snapshot_is_unique_per_company_document():
    assert 'UniqueConstraint("company_id", "document_kind", "document_id"' in MODEL
    assert 'uq_tax_snapshot_document' in MODEL


def test_snapshot_captures_rule_values_not_live_rule_pointer_only():
    assert "rules= [" not in SERVICE
    assert "rules=[" in SERVICE
    for field in ("code", "tax_type", "rate", "effective_from", "effective_to", "version", "source_reference"):
        assert f'"{field}"' in SERVICE


def test_snapshot_cannot_be_silently_recreated():
    assert "Tax snapshot already exists for this document" in SERVICE


def test_snapshot_migration_is_after_global_jurisdiction():
    assert 'down_revision = "20260914_global_jurisdiction"' in MIGRATION
    assert 'revision = "20260914_tax_snapshots"' in MIGRATION


def test_global_jurisdiction_is_after_commerce_ppv_head():
    assert 'down_revision = "20260914_commerce_ppv"' in GLOBAL_MIGRATION
