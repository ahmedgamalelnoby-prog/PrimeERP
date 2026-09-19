from types import SimpleNamespace

from app.modules.shipping.accounting_service import ShippingAccountingService


def test_shipping_accounting_role_map_covers_financial_event_roles():
    carrier = SimpleNamespace(
        fee_account_id=301,
        settlement_account_id=302,
        cash_account_id=303,
    )
    settings = SimpleNamespace(
        ar_account_id=101,
        sales_account_id=102,
    )
    mapping = ShippingAccountingService._account_map(carrier, settings)

    assert mapping["customer_receivable"] == 101
    assert mapping["sales_revenue"] == 102
    assert mapping["shipping_revenue"] == 102
    assert mapping["shipping_expense"] == 301
    assert mapping["cod_commission_expense"] == 301
    assert mapping["payment_withdrawal_fee_expense"] == 301
    assert mapping["carrier_payable"] == 302
    assert mapping["carrier_cod_receivable"] == 302
    assert mapping["bank_cash"] == 303
