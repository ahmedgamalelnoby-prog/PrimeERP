from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "app/modules/jurisdiction/commerce_guard.py"
ROUTER = ROOT / "app/modules/commerce/router.py"


def test_commerce_guard_covers_financial_document_types():
    text = GUARD.read_text(encoding="utf-8")
    assert '"invoice", "credit_note"' in text
    assert '"bill", "debit_note"' in text
    assert "TaxSnapshotService" in text
    assert "validate_snapshot_tax(document, snapshot)" in text


def test_confirmation_routes_capture_snapshot_before_confirm():
    text = ROUTER.read_text(encoding="utf-8")
    assert "capture_document_tax_snapshot(db, obj, kind=\"sale\")" in text
    assert "capture_document_tax_snapshot(db, obj, kind=\"purchase\")" in text
    assert text.index("capture_document_tax_snapshot(db, obj, kind=\"sale\")") < text.index("commerce_service.confirm(db, company_id, document_id, \"sale\"")
    assert text.index("capture_document_tax_snapshot(db, obj, kind=\"purchase\")") < text.index("commerce_service.confirm(db, company_id, document_id, \"purchase\"")


def test_tax_snapshot_is_not_recomputed_by_accounting_service():
    text = (ROOT / "app/modules/commerce/accounting_service.py").read_text(encoding="utf-8")
    assert "TaxSnapshotService" not in text
    assert "source_entity=\"sales_invoice\"" in text
    assert "source_entity=\"purchase_bill\"" in text


def test_payment_workflow_requires_snapshot_and_validates_wht():
    text = (ROOT / "app/modules/commerce/payment_workflow.py").read_text(encoding="utf-8")
    assert "TaxSnapshot" in text
    assert "Tax snapshot is required before posting payment" in text
    assert "validate_payment_wht(candidate, snapshot)" in text
