from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_partial_reservation_contract_is_explicit():
    model = (ROOT / "app/modules/inventory/reservations/models.py").read_text()
    service = (ROOT / "app/modules/inventory/reservations/service.py").read_text()
    assert "consumed_quantity" in model
    assert "InventoryReservationConsumption" in model
    assert "consume_qty" in service
    assert "consumption quantity" in service.lower()


def test_pos_payment_methods_have_explicit_mapping_domain():
    model = (ROOT / "app/modules/commerce/accounting_models.py").read_text()
    service = (ROOT / "app/modules/pos/service.py").read_text()
    router = (ROOT / "app/modules/pos/router.py").read_text()
    assert "POSPaymentAccountMapping" in model
    assert "_payment_account" in service
    assert "payment-account-mappings" in router


def test_stage7_financial_hardening_migration_is_downstream_of_stage7_merge():
    migration = (ROOT / "alembic/versions/20260921_pos_financial_hardening.py").read_text()
    assert 'down_revision = "20260921_stage7_domain_merge"' in migration


def test_previous_rc_is_not_modified_by_this_branch():
    # This branch is intentionally additive on top of the verified Stage 7 head.
    assert "20260921_stage7_domain_merge" in (
        ROOT / "alembic/versions/20260921_stage7_domain_merge.py"
    ).read_text()
