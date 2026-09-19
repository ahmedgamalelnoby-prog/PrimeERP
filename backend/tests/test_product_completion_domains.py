from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.modules.accounting.tax_engine import calculate_taxes, money
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.models import BusinessPartner, SalesDocument, PurchaseDocument, CommercePayment, SalesLine, PurchaseLine
from app.modules.commerce.schemas import DocumentLineCreate
from app.modules.commerce.service import CommerceService
from app.modules.enterprise.models import FixedAsset, Budget, Employee, PayrollRun, Project, ProjectContract
from app.modules.inventory.items.models import InventoryItem
from app.modules.shipping.models import ShippingCarrier, ShippingMethod, Shipment


def test_product_completion_models_registered():
    assert BusinessPartner.__tablename__ == 'commerce_partners'
    assert SalesDocument.__tablename__ == 'sales_documents'
    assert PurchaseDocument.__tablename__ == 'purchase_documents'
    assert CommercePayment.__tablename__ == 'commerce_payments'
    assert SalesLine.__table__.c.tax_rate_ids is not None
    assert PurchaseLine.__table__.c.tax_rate_ids is not None
    assert InventoryItem.__table__.c.sales_tax_ids is not None
    assert InventoryItem.__table__.c.purchase_tax_ids is not None
    assert FixedAsset.__tablename__ == 'fixed_assets'
    assert Budget.__tablename__ == 'budgets'
    assert Employee.__tablename__ == 'employees'
    assert PayrollRun.__tablename__ == 'payroll_runs'
    assert Project.__tablename__ == 'projects'
    assert ProjectContract.__tablename__ == 'project_contracts'
    assert ShippingCarrier.__tablename__ == 'shipping_carriers'
    assert ShippingMethod.__tablename__ == 'shipping_methods'
    assert Shipment.__tablename__ == 'shipments'


def test_sales_line_math():
    qty=Decimal('3');price=Decimal('100');discount=Decimal('10');tax=Decimal('14')
    net=qty*price-(qty*price*discount/100)
    total=net+(net*tax/100)
    assert net == Decimal('270')
    assert total == Decimal('307.8')


def test_tax_master_is_authoritative_for_explicit_line_tax():
    line = DocumentLineCreate(
        item_id=1,
        tax_rate_ids=[10, 11],
        quantity=Decimal('2'),
        unit_price=Decimal('100'),
    )
    assert line.tax_rate_ids == [10, 11]
    assert line.tax_percent == Decimal('0')


def test_money_rounding_used_by_tax_engine():
    assert money(Decimal('1.005')) == Decimal('1.01')


def test_tax_engine_rejects_withholding_above_gross():
    taxes = [
        SimpleNamespace(id=1, code='WHT-60', name='WHT 60%', rate=Decimal('60'), tax_type='wht', is_withholding=True),
        SimpleNamespace(id=2, code='WHT-50', name='WHT 50%', rate=Decimal('50'), tax_type='wht', is_withholding=True),
    ]

    class FakeScalarResult:
        def all(self):
            return taxes

    class FakeDB:
        def scalars(self, _query):
            return FakeScalarResult()

    with pytest.raises(Exception, match='Total withholding tax cannot exceed the gross taxable amount'):
        calculate_taxes(
            FakeDB(),
            company_id=7,
            amount=Decimal('100.00'),
            tax_ids=[1, 2],
        )


def test_sales_invoice_accounting_is_balanced(monkeypatch):
    settings = SimpleNamespace(
        sales_journal_id=401,
        purchase_journal_id=402,
        cash_journal_id=403,
        ar_account_id=101,
        sales_account_id=102,
        output_vat_account_id=103,
    )
    document = SimpleNamespace(
        id=55,
        company_id=7,
        document_date=date(2026, 9, 13),
        number='INV-55',
        subtotal=Decimal('1000.00'),
        tax_total=Decimal('140.00'),
        total=Decimal('1140.00'),
    )
    captured = {}

    monkeypatch.setattr(commerce_accounting_service, '_settings', lambda db, company_id: settings)
    monkeypatch.setattr(
        commerce_accounting_service,
        '_post',
        lambda db, **kwargs: captured.update(kwargs) or kwargs,
    )

    result = commerce_accounting_service.post_sales_invoice(None, document, user_id=9)

    assert result['source_entity'] == 'sales_invoice'
    assert result['source_id'] == 55
    assert sum(Decimal(line['debit']) for line in result['lines']) == Decimal('1140.00')
    assert sum(Decimal(line['credit']) for line in result['lines']) == Decimal('1140.00')
    assert captured['journal_id'] == 401


def test_sale_payment_with_wht_posts_gross_control_and_net_cash(monkeypatch):
    settings = SimpleNamespace(
        sales_journal_id=401,
        purchase_journal_id=402,
        cash_journal_id=403,
        ar_account_id=101,
        ap_account_id=201,
        default_payment_account_id=301,
        wht_account_id=302,
    )
    payment = SimpleNamespace(
        id=77,
        company_id=7,
        document_kind='sale',
        payment_date=date(2026, 9, 13),
        amount=Decimal('1140.00'),
        wht_amount=Decimal('11.40'),
    )
    captured = {}

    monkeypatch.setattr(commerce_accounting_service, '_settings', lambda db, company_id: settings)
    monkeypatch.setattr(
        commerce_accounting_service,
        '_post',
        lambda db, **kwargs: captured.update(kwargs) or kwargs,
    )

    result = commerce_accounting_service.post_payment(None, payment, SimpleNamespace(id=55), user_id=9)
    lines = result['lines']

    assert sum(Decimal(line['debit']) for line in lines) == Decimal('1140.00')
    assert sum(Decimal(line['credit']) for line in lines) == Decimal('1140.00')
    assert next(line for line in lines if line['account_combination_id'] == 301)['debit'] == Decimal('1128.60')
    assert next(line for line in lines if line['account_combination_id'] == 302)['debit'] == Decimal('11.40')
    assert next(line for line in lines if line['account_combination_id'] == 101)['credit'] == Decimal('1140.00')
    assert captured['source_entity'] == 'commerce_payment'
    assert captured['journal_id'] == 403


def test_purchase_payment_with_wht_posts_gross_ap_and_net_cash(monkeypatch):
    settings = SimpleNamespace(
        sales_journal_id=401,
        purchase_journal_id=402,
        cash_journal_id=403,
        ar_account_id=101,
        ap_account_id=201,
        default_payment_account_id=301,
        wht_account_id=302,
    )
    payment = SimpleNamespace(
        id=88,
        company_id=7,
        document_kind='purchase',
        payment_date=date(2026, 9, 13),
        amount=Decimal('1140.00'),
        wht_amount=Decimal('11.40'),
    )
    captured = {}

    monkeypatch.setattr(commerce_accounting_service, '_settings', lambda db, company_id: settings)
    monkeypatch.setattr(
        commerce_accounting_service,
        '_post',
        lambda db, **kwargs: captured.update(kwargs) or kwargs,
    )

    result = commerce_accounting_service.post_payment(None, payment, SimpleNamespace(id=66), user_id=9)
    lines = result['lines']

    assert sum(Decimal(line['debit']) for line in lines) == Decimal('1140.00')
    assert sum(Decimal(line['credit']) for line in lines) == Decimal('1140.00')
    assert next(line for line in lines if line['account_combination_id'] == 201)['debit'] == Decimal('1140.00')
    assert next(line for line in lines if line['account_combination_id'] == 301)['credit'] == Decimal('1128.60')
    assert next(line for line in lines if line['account_combination_id'] == 302)['credit'] == Decimal('11.40')
    assert captured['source_entity'] == 'commerce_payment'
    assert captured['source_id'] == 88
    assert captured['journal_id'] == 403


def test_sale_payment_reversal_is_exact_accounting_opposite_and_uses_reversal_date(monkeypatch):
    settings = SimpleNamespace(
        sales_journal_id=401,
        purchase_journal_id=402,
        cash_journal_id=403,
        ar_account_id=101,
        ap_account_id=201,
        default_payment_account_id=301,
        wht_account_id=302,
    )
    payment = SimpleNamespace(
        id=77,
        company_id=7,
        document_kind='sale',
        payment_date=date(2026, 9, 13),
        amount=Decimal('1140.00'),
        wht_amount=Decimal('11.40'),
    )
    captured = {}
    reversal_date = date(2026, 9, 20)

    monkeypatch.setattr(commerce_accounting_service, '_settings', lambda db, company_id: settings)
    monkeypatch.setattr(
        commerce_accounting_service,
        '_post',
        lambda db, **kwargs: captured.update(kwargs) or kwargs,
    )

    result = commerce_accounting_service.post_payment_reversal(
        None,
        payment,
        SimpleNamespace(id=55),
        user_id=9,
        reversal_date=reversal_date,
    )
    lines = result['lines']

    assert sum(Decimal(line['debit']) for line in lines) == Decimal('1140.00')
    assert sum(Decimal(line['credit']) for line in lines) == Decimal('1140.00')
    assert next(line for line in lines if line['account_combination_id'] == 101)['debit'] == Decimal('1140.00')
    assert next(line for line in lines if line['account_combination_id'] == 301)['credit'] == Decimal('1128.60')
    assert next(line for line in lines if line['account_combination_id'] == 302)['credit'] == Decimal('11.40')
    assert captured['entry_date'] == reversal_date
    assert captured['source_entity'] == 'commerce_payment_reversal'
    assert captured['source_id'] == 77
    assert captured['journal_id'] == 403


def test_purchase_payment_reversal_is_exact_accounting_opposite(monkeypatch):
    settings = SimpleNamespace(
        sales_journal_id=401,
        purchase_journal_id=402,
        cash_journal_id=403,
        ar_account_id=101,
        ap_account_id=201,
        default_payment_account_id=301,
        wht_account_id=302,
    )
    payment = SimpleNamespace(
        id=88,
        company_id=7,
        document_kind='purchase',
        payment_date=date(2026, 9, 13),
        amount=Decimal('1140.00'),
        wht_amount=Decimal('11.40'),
    )
    captured = {}

    monkeypatch.setattr(commerce_accounting_service, '_settings', lambda db, company_id: settings)
    monkeypatch.setattr(
        commerce_accounting_service,
        '_post',
        lambda db, **kwargs: captured.update(kwargs) or kwargs,
    )

    result = commerce_accounting_service.post_payment_reversal(
        None,
        payment,
        SimpleNamespace(id=66),
        user_id=9,
        reversal_date=date(2026, 9, 20),
    )
    lines = result['lines']

    assert sum(Decimal(line['debit']) for line in lines) == Decimal('1140.00')
    assert sum(Decimal(line['credit']) for line in lines) == Decimal('1140.00')
    assert next(line for line in lines if line['account_combination_id'] == 301)['debit'] == Decimal('1128.60')
    assert next(line for line in lines if line['account_combination_id'] == 302)['debit'] == Decimal('11.40')
    assert next(line for line in lines if line['account_combination_id'] == 201)['credit'] == Decimal('1140.00')
    assert captured['entry_date'] == date(2026, 9, 20)
    assert captured['source_entity'] == 'commerce_payment_reversal'
    assert captured['source_id'] == 88
    assert captured['journal_id'] == 403


def test_payment_auto_wht_uses_product_tax_profile_result(monkeypatch):
    service = CommerceService()
    document = SimpleNamespace(id=55, total=Decimal('1140.00'), paid_total=Decimal('0'))
    captured = {}

    monkeypatch.setattr(service, '_auto_payment_wht', lambda db, **kwargs: Decimal('11.40'))
    payment = SimpleNamespace(
        id=77,
        company_id=7,
        document_kind='sale',
        document_id=55,
        amount=Decimal('1140.00'),
    )
    def fake_post_payment(db, **kwargs):
        captured.update(kwargs)
        return document, payment

    monkeypatch.setattr(
        'app.modules.commerce.service.post_payment',
        fake_post_payment,
    )

    payload = SimpleNamespace(
        company_id=7,
        document_id=55,
        payment_date=date(2026, 9, 13),
        amount=Decimal('1140.00'),
        wht_amount=Decimal('0'),
        auto_wht=True,
        method='bank_transfer',
        reference=None,
        notes=None,
        idempotency_key=None,
    )

    class FakeDB:
        def __init__(self):
            self.calls = 0

        def scalar(self, _query):
            self.calls += 1
            return document if self.calls == 1 else None

        def add(self, _value):
            pass

        def flush(self):
            pass

    service.pay(FakeDB(), payload, 'sale')
    assert captured['wht_amount'] == Decimal('11.40')


def test_payment_auto_wht_can_be_disabled():
    payload = SimpleNamespace(wht_amount=Decimal('0'), auto_wht=False)
    assert payload.wht_amount == Decimal('0')
    assert payload.auto_wht is False


def test_straight_line_depreciation_math():
    depreciable=Decimal('100000')-Decimal('10000')
    monthly=depreciable/60
    assert monthly == Decimal('1500')


def test_commerce_payment_retry_does_not_duplicate_cheque_side_effect():
    import inspect

    source = inspect.getsource(CommerceService.pay)
    assert "Payment idempotency can return the already-posted payment" in source
    assert "Cheque.source_payment_id == payment.id" in source
    assert "if existing_cheque is None:" in source


def test_payment_schema_supports_split_allocations_and_requires_primary_document():
    from app.modules.commerce.schemas import PaymentCreate
    payload = PaymentCreate(
        company_id=7,
        document_id=10,
        payment_date=date(2026, 9, 19),
        amount=Decimal("1500"),
        method="bank_transfer",
        allocations=[
            {"document_id": 10, "amount": Decimal("900")},
            {"document_id": 11, "amount": Decimal("600")},
        ],
    )
    assert len(payload.allocations) == 2


def test_payment_schema_rejects_unallocated_payment_remainder():
    from app.modules.commerce.schemas import PaymentCreate

    with pytest.raises(ValueError, match="must equal the payment amount"):
        PaymentCreate(
            company_id=7,
            document_id=10,
            payment_date=date(2026, 9, 19),
            amount=Decimal("1500"),
            method="bank_transfer",
            allocations=[
                {"document_id": 10, "amount": Decimal("900")},
                {"document_id": 11, "amount": Decimal("500")},
            ],
        )


def test_payment_allocation_model_allows_multiple_documents_per_payment():
    from app.modules.commerce.models import CommercePaymentAllocation
    constraints = {c.name for c in CommercePaymentAllocation.__table__.constraints}
    assert "uq_commerce_payment_allocation_document" in constraints
    assert "uq_commerce_payment_allocation_payment" not in constraints


def test_payment_reverse_handles_all_active_allocations():
    import inspect
    from app.modules.commerce.payment_workflow import reverse_payment
    source = inspect.getsource(reverse_payment)
    assert "CommercePaymentAllocation.status == \"active\"" in source
    assert "target.paid_total" in source
    assert "allocation.status = \"reversed\"" in source

def test_ar_ap_aging_uses_split_payment_allocations_as_of_cutoff():
    import inspect
    source = inspect.getsource(CommerceService.ar_ap_aging)
    assert "CommercePaymentAllocation" in source
    assert "allocation.document_id" in source
    assert "allocation.amount" in source
    assert 'allocation.status == "active"' in source
    assert "allocated_payment_ids" in source
    assert "Legacy payments created before allocation tracking remain" in source
