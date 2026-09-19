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

def test_partner_open_balance_is_allocation_aware_and_historical():
    import inspect
    source = inspect.getsource(CommerceService.partner_open_balance)
    assert "CommercePaymentAllocation" in source
    assert "payments_by_document" in source
    assert "allocation.document_id" in source
    assert "allocation.amount" in source
    assert "payment.payment_date < before_date" in source
    assert "paid_total" not in source


def test_inventory_outbound_standard_cost_is_policy_authoritative():
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    item = SimpleNamespace(costing_method="standard", standard_cost=Decimal("25.00"), purchase_price=Decimal("30.00"))
    warehouse = SimpleNamespace(average_cost=Decimal("99.00"))

    assert InventoryStockMoveService._outbound_unit_cost(item, warehouse) == Decimal("25.00")


def test_inventory_outbound_weighted_average_cost_is_policy_authoritative():
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    item = SimpleNamespace(costing_method="weighted_average", standard_cost=Decimal("25.00"), purchase_price=Decimal("30.00"))
    warehouse = SimpleNamespace(average_cost=Decimal("37.50"))

    assert InventoryStockMoveService._outbound_unit_cost(item, warehouse) == Decimal("37.50")


def test_inventory_fifo_weighted_cost_uses_exact_layer_allocations():
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    allocations = [
        (SimpleNamespace(id=1), Decimal("2"), Decimal("10")),
        (SimpleNamespace(id=2), Decimal("3"), Decimal("20")),
    ]

    assert InventoryStockMoveService._weighted_cost(allocations) == Decimal("16")


def test_inventory_fifo_recalculation_and_destination_reversal_are_variant_scoped():
    import inspect
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    recalc = inspect.getsource(InventoryStockMoveService._recalculate_average_cost)
    reverse = inspect.getsource(InventoryStockMoveService._reverse_fifo_destination_layers)

    assert "InventoryCostLayer.variant_id == variant_id" in recalc
    assert "InventoryCostLayer.variant_id == variant_id" in reverse
    assert "InventoryCostLayer.variant_id.is_(None)" in recalc
    assert "InventoryCostLayer.variant_id.is_(None)" in reverse


def test_stock_move_reservation_contract_is_atomic_and_exact():
    import inspect
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    source = inspect.getsource(InventoryStockMoveService.post)
    assert "InventoryReservation" in source
    assert "with_for_update()" in source
    assert "reservation.status != " + '"active"' in source
    assert "reservation.item_id != move.item_id" in source
    assert "Decimal(reservation.quantity) != Decimal(move.quantity)" in source
    assert "source_balance.quantity_reserved -= quantity" in source
    assert "warehouse_source.quantity_reserved -= quantity" in source
    assert 'reservation.status = "consumed"' in source


def test_stock_move_reversal_restores_consumed_reservation():
    import inspect
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    source = inspect.getsource(InventoryStockMoveService.reverse)
    assert "Linked reservation must be consumed before movement reversal" in source
    assert "source_balance.quantity_reserved += quantity" in source
    assert "warehouse_source.quantity_reserved += quantity" in source
    assert 'reservation.status = "active"' in source


def test_inventory_transfer_allows_distinct_locations_in_same_warehouse():
    import inspect
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService

    source = inspect.getsource(InventoryStockMoveService.create_draft)
    assert 'if source.warehouse_id == destination.warehouse_id and source.id == destination.id:' in source
    assert 'raise ValueError("Source and destination locations must differ")' in source
    assert 'Use a direct stock move for an intra-warehouse location transfer' not in source


def test_inventory_balance_creation_is_race_safe():
    import inspect
    from app.modules.inventory.stock_moves.service import InventoryStockMoveService
    from app.modules.inventory.reservations.service import InventoryReservationService

    stock_source = inspect.getsource(InventoryStockMoveService._location_balance)
    warehouse_source = inspect.getsource(InventoryStockMoveService._warehouse_stock)
    reservation_balance = inspect.getsource(InventoryReservationService._locked_balance)
    reservation_warehouse = inspect.getsource(InventoryReservationService._locked_warehouse_stock)

    for source in (stock_source, warehouse_source, reservation_balance, reservation_warehouse):
        assert "on_conflict_do_nothing" in source
        assert "pg_insert" in source
        assert "Unable to create or lock" in source or "db.scalar(stmt.with_for_update())" in source


def test_inventory_reservation_variant_validation_uses_product_variant_is_active():
    import inspect
    from app.modules.inventory.reservations.service import InventoryReservationService

    source = inspect.getsource(InventoryReservationService._validate_variant)
    assert "ProductVariant.is_active.is_(True)" in source
    assert "ProductVariant.active.is_(True)" not in source
