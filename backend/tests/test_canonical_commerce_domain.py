from decimal import Decimal

from app.modules.catalog.domain import CompositionLine, ItemKind, ProductComposition, ProductKind
from app.modules.integrations.commerce_contracts import (
    CanonicalOrder,
    CanonicalOrderLine,
    CanonicalPayment,
    CanonicalShipment,
    normalize_payment_method,
)
from app.modules.accounting.transaction_contract import FinancialImpact


def test_item_product_and_composition_are_distinct():
    line = CompositionLine(component_item_id=10, quantity=Decimal("30"))
    composition = ProductComposition(product_id=100, lines=(line,))
    assert ItemKind.RAW_MATERIAL.value == "raw_material"
    assert ProductKind.MANUFACTURED.value == "manufactured"
    assert composition.material_cost({10: Decimal("2")}) == Decimal("60")


def test_recipe_waste_is_included_in_material_cost():
    line = CompositionLine(
        component_item_id=10,
        quantity=Decimal("100"),
        waste_percentage=Decimal("5"),
    )
    composition = ProductComposition(product_id=100, lines=(line,))
    assert composition.material_cost({10: Decimal("1.5")}) == Decimal("157.5")


def test_canonical_order_exposes_revenue_and_cod_without_platform_logic():
    order = CanonicalOrder(
        platform="salla",
        connection_id=1,
        external_order_id="S-100",
        order_date="2026-09-19",
        currency="EGP",
        customer_external_id="C-1",
        status="confirmed",
        lines=(
            CanonicalOrderLine(
                external_line_id="L-1",
                sku="P-1",
                item_external_id="10",
                variant_external_id=None,
                quantity=Decimal("2"),
                unit_price=Decimal("100"),
                discount=Decimal("10"),
            ),
        ),
        payments=(CanonicalPayment(method="cod", amount=Decimal("210"), cod_amount=Decimal("210")),),
        shipments=(CanonicalShipment(
            external_shipment_id="SH-1",
            external_carrier_id="AR-1",
            carrier_name="Aramex",
            tracking_number="TR-1",
            status="out_for_delivery",
            raw_status="to_be_reattempted",
            payment_method="cod",
            shipping_fee=Decimal("20"),
            customer_shipping_fee=Decimal("10"),
            cod_amount=Decimal("210"),
        ),),
    )
    assert order.merchandise_revenue == Decimal("190")
    assert order.shipping_revenue == Decimal("10")
    assert order.total_cod == Decimal("210")


def test_payment_normalization_is_provider_neutral():
    assert normalize_payment_method("Cash On Delivery") == "cod"
    assert normalize_payment_method("MADA") == "prepaid"
    assert normalize_payment_method("Bank Transfer") == "bank_transfer"


def test_financial_impact_derives_gross_profit():
    impact = FinancialImpact(revenue=Decimal("1000"), cogs=Decimal("600"))
    assert impact.gross_profit == Decimal("400")
