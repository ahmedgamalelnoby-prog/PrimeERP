import pytest

from app.modules.egyptian_einvoice.crud import create_document


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar(self, _query):
        return self.value


class _DB:
    def __init__(self, value):
        self.value = value

    def scalar(self, _query):
        return self.value

    def add(self, _obj):
        pass

    def flush(self):
        pass


def test_einvoice_rejects_unsupported_source_type():
    with pytest.raises(ValueError, match="Unsupported ETA source type"):
        create_document(_DB(None), company_id=7, source_type="purchase_bill", source_id=10, document_type="invoice", internal_number="INV-10", signed_payload="{}")


def test_einvoice_rejects_source_from_another_company():
    with pytest.raises(ValueError, match="does not belong to the company"):
        create_document(_DB(None), company_id=7, source_type="sales_document", source_id=10, document_type="invoice", internal_number="INV-10", signed_payload="{}")


def test_einvoice_rejects_document_type_mismatch():
    source = type("Source", (), {"document_type": "credit_note"})()
    with pytest.raises(ValueError, match="does not match"):
        create_document(_DB(source), company_id=7, source_type="sales_document", source_id=10, document_type="invoice", internal_number="INV-10", signed_payload="{}")


def test_einvoice_requires_valid_signed_json():
    source = type("Source", (), {"document_type": "invoice"})()
    with pytest.raises(ValueError, match="valid JSON"):
        create_document(_DB(source), company_id=7, source_type="sales_document", source_id=10, document_type="invoice", internal_number="INV-10", signed_payload="not-json")
