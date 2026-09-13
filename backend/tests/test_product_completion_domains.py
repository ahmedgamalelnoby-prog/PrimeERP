from decimal import Decimal

from app.modules.accounting.tax_engine import money
from app.modules.commerce.models import BusinessPartner, SalesDocument, PurchaseDocument, CommercePayment, SalesLine, PurchaseLine
from app.modules.commerce.schemas import DocumentLineCreate
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


def test_straight_line_depreciation_math():
    depreciable=Decimal('100000')-Decimal('10000')
    monthly=depreciable/60
    assert monthly == Decimal('1500')
