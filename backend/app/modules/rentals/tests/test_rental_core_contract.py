from datetime import date
from decimal import Decimal
from app.modules.rentals.service import RentalService

def test_revenue_share_charge_math():
    class C:
        pricing_type="revenue_share"; fixed_rent=0; minimum_guarantee=0; revenue_share_percent=10; maintenance_amount=100; vat_percent=14; wht_percent=3
    base=Decimal("1000"); maintenance=Decimal("100"); vat=(base+maintenance)*Decimal("14")/100; wht=base*Decimal("3")/100
    assert base+maintenance+vat-wht == Decimal("1240")
