from decimal import Decimal

import pytest

from app.modules.inventory.reservations.schemas import ReservationCreate


def test_reservation_requires_positive_quantity():
    with pytest.raises(ValueError):
        ReservationCreate(
            company_id=1,
            item_id=1,
            location_id=1,
            quantity=Decimal("0"),
            source_module="sales",
            source_entity="sales_order",
            source_id="SO-1",
        )


def test_reservation_source_is_explicit():
    reservation = ReservationCreate(
        company_id=1,
        item_id=2,
        location_id=3,
        quantity=Decimal("5"),
        source_module="sales",
        source_entity="sales_order_line",
        source_id="101",
    )
    assert reservation.source_module == "sales"
    assert reservation.source_entity == "sales_order_line"
    assert reservation.source_id == "101"
