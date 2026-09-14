from types import SimpleNamespace

import pytest

from app.modules.integrations import salla_erp_service as service


class ScalarOnlyDB:
    def __init__(self, value=None):
        self.value = value
        self.scalar_calls = 0

    def scalar(self, _statement):
        self.scalar_calls += 1
        return self.value


def test_execute_salla_order_does_not_reprocess_reversed_order(monkeypatch):
    order = SimpleNamespace(
        company_id=10,
        connection_id=20,
        external_id="S-100",
        erp_status="reversed",
        erp_entity_id=501,
    )
    db = ScalarOnlyDB()
    monkeypatch.setattr(service, "_mapping", lambda *args: SimpleNamespace(local_id=9001))

    result = service.execute_salla_order(db, order, user_id=7)

    assert result == {
        "status": "already_reversed",
        "sales_document_id": 501,
        "credit_note_id": 9001,
    }
    assert db.scalar_calls == 0


def test_processed_salla_order_with_missing_invoice_fails_loudly():
    order = SimpleNamespace(
        company_id=10,
        connection_id=20,
        external_id="S-101",
        erp_status="processed",
        erp_entity_id=502,
    )
    db = ScalarOnlyDB(None)

    with pytest.raises(service.SallaERPExecutionError, match="missing ERP invoice"):
        service.execute_salla_order(db, order, user_id=7)
