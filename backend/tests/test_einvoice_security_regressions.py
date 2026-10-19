import pytest

from app.modules.egyptian_einvoice.crud import create_document


class _Company:
    def __init__(self, tenant_id):
        self.id = 7
        self.tenant_id = tenant_id
        self.is_active = True
        self.eta_taxpayer_id = "TAX-COMPANY"
        self.tax_id = "TAX-COMPANY"


class _Partner:
    id = 12
    company_id = 7
    partner_type = "customer"
    eta_party_id = "TAX-CUSTOMER"
    tax_number = "TAX-CUSTOMER"


class _DB:
    def __init__(self, company_tenant_id, source, partner=None):
        self.company = _Company(company_tenant_id) if company_tenant_id is not None else None
        self.source = source
        self.partner = partner or _Partner()
        self._calls = 0

    def scalar(self, _query):
        self._calls += 1
        if self._calls == 1:
            return self.company
        if self._calls == 2:
            return self.source
        return self.partner

    def add(self, _obj):
        pass

    def flush(self):
        pass


def test_einvoice_rejects_unsupported_source_type():
    with pytest.raises(ValueError, match="Unsupported ETA source type"):
        create_document(
            _DB(7, None),
            tenant_id=7,
            company_id=7,
            source_type="purchase_bill",
            source_id=10,
            document_type="invoice",
            internal_number="INV-10",
            signed_payload="{}",
        )


def test_einvoice_rejects_source_from_another_company():
    with pytest.raises(ValueError, match="does not belong to the company"):
        create_document(
            _DB(7, None),
            tenant_id=7,
            company_id=7,
            source_type="sales_document",
            source_id=10,
            document_type="invoice",
            internal_number="INV-10",
            signed_payload="{}",
        )


def test_einvoice_rejects_company_from_another_tenant():
    with pytest.raises(ValueError, match="does not belong to the tenant"):
        create_document(
            _DB(None, None),
            tenant_id=7,
            company_id=7,
            source_type="sales_document",
            source_id=10,
            document_type="invoice",
            internal_number="INV-10",
            signed_payload="{}",
        )


def test_einvoice_rejects_document_type_mismatch_before_customer_lookup():
    source = type("Source", (), {"document_type": "credit_note"})()
    with pytest.raises(ValueError, match="does not match"):
        create_document(
            _DB(7, source),
            tenant_id=7,
            company_id=7,
            source_type="sales_document",
            source_id=10,
            document_type="invoice",
            internal_number="INV-10",
            signed_payload="{}",
        )


def test_einvoice_requires_valid_signed_json_before_customer_lookup():
    source = type("Source", (), {"document_type": "invoice"})()
    with pytest.raises(ValueError, match="valid JSON"):
        create_document(
            _DB(7, source),
            tenant_id=7,
            company_id=7,
            source_type="sales_document",
            source_id=10,
            document_type="invoice",
            internal_number="INV-10",
            signed_payload="not-json",
        )


def test_einvoice_rejects_signed_payload_identity_mismatch():
    source = type("Source", (), {"document_type": "invoice", "partner_id": 12})()
    payload = '{"issuer":{"id":"WRONG"},"receiver":{"id":"TAX-CUSTOMER"}}'
    with pytest.raises(ValueError, match="issuer.id"):
        create_document(
            _DB(7, source),
            tenant_id=7,
            company_id=7,
            source_type="sales_document",
            source_id=10,
            document_type="invoice",
            internal_number="INV-10",
            signed_payload=payload,
        )
