from decimal import Decimal
from pathlib import Path
from app.modules.jurisdiction.service import JurisdictionEngine

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "app/modules/jurisdiction/service.py"
SNAPSHOT = ROOT / "app/modules/jurisdiction/snapshot_service.py"
MODELS = ROOT / "app/modules/jurisdiction/models.py"
MIGRATION = ROOT / "alembic/versions/20260914_tax_snapshots.py"


def test_tax_math_is_deterministic_and_non_negative():
    assert JurisdictionEngine.calculate_tax(Decimal("1000"), Decimal("14")) == Decimal("140.0000")
    assert JurisdictionEngine.calculate_tax(Decimal("99.99"), Decimal("15")) == Decimal("14.9985")


def test_tax_math_rejects_negative_values():
    try: JurisdictionEngine.calculate_tax(Decimal("-1"), Decimal("15"))
    except ValueError: pass
    else: raise AssertionError("negative tax base must be rejected")


def test_global_model_is_effective_dated_and_has_snapshot():
    text = MODELS.read_text(encoding="utf-8")
    assert "effective_from" in text and "effective_to" in text and "country_code" in text
    assert "class TaxSnapshot" in text and "UniqueConstraint(\"company_id\", \"document_kind\", \"document_id\"" in text
    assert "EG" not in text


def test_snapshot_service_is_present_and_locks_existing_snapshot():
    text = SNAPSHOT.read_text(encoding="utf-8")
    assert "class TaxSnapshotService" in text
    assert "TaxSnapshot" in text and "effective_from" in text and "source_reference" in text and "version" in text
    assert "with_for_update()" in text
    assert "TaxSnapshot already" not in text


def test_snapshot_migration_is_after_jurisdiction():
    text = MIGRATION.read_text(encoding="utf-8")
    assert 'down_revision = "20260914_global_jurisdiction"' in text
    assert '"tax_snapshots"' in text
    assert '"uq_tax_snapshot_document"' in text


def test_tax_rule_conditions_are_evaluated():
    text = SERVICE.read_text(encoding="utf-8")
    assert "def _condition_matches" in text
    assert '"eq"' in text and '"in"' in text and '"not_in"' in text
    assert "ctx.facts" in text
