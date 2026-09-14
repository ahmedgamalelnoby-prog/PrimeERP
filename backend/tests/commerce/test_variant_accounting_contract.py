from decimal import Decimal

from app.modules.commerce.schemas import DocumentCreate, DocumentLineCreate


def test_document_line_preserves_variant_dimension_for_commerce():
    line = DocumentLineCreate(
        item_id=10,
        variant_id=22,
        quantity=Decimal("2"),
        unit_price=Decimal("150"),
    )
    assert line.variant_id == 22


def test_purchase_and_sales_documents_accept_the_same_variant_line_contract():
    sale = DocumentCreate(
        company_id=1,
        partner_id=2,
        document_type="invoice",
        number="SI-1",
        document_date="2026-09-14",
        lines=[DocumentLineCreate(item_id=10, variant_id=22, quantity=1, unit_price=100)],
    )
    purchase = DocumentCreate(
        company_id=1,
        partner_id=3,
        document_type="bill",
        number="PB-1",
        document_date="2026-09-14",
        lines=[DocumentLineCreate(item_id=10, variant_id=22, quantity=1, unit_price=60)],
    )
    assert sale.lines[0].variant_id == purchase.lines[0].variant_id == 22
