from app.modules.shipping.status_service import DEFAULT_STATUSES


def test_default_shipping_lifecycle_has_financial_delivery_rules():
    statuses = {row[0]: row for row in DEFAULT_STATUSES}
    assert list(statuses)[:4] == ["pending", "preparing", "packing", "shipped"]
    assert "recognize_revenue" in statuses["delivered"][5]
    assert "recognize_shipping_revenue" in statuses["delivered"][5]
    assert "recognize_shipping_cost" in statuses["delivered"][5]
    assert "create_cod_receivable" in statuses["delivered"][5]
    assert "reverse_revenue" in statuses["returned"][5]
    assert "reverse_cod_receivable" in statuses["returned"][5]


def test_default_status_codes_are_unique():
    codes = [row[0] for row in DEFAULT_STATUSES]
    assert len(codes) == len(set(codes))


def test_delivered_default_includes_carrier_withdrawal_fee():
    from app.modules.shipping.status_service import DEFAULT_STATUSES
    delivered = next(row for row in DEFAULT_STATUSES if row[0] == "delivered")
    assert "recognize_payment_withdrawal_fee" in delivered[5]
