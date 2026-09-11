from app.modules.inventory.transfers.schemas import TransferCreate, TransferLineCreate


def test_transfer_payload_supports_cross_warehouse_lines():
    payload = TransferCreate(
        company_id=1,
        source_warehouse_id=10,
        destination_warehouse_id=20,
        reference="TR-001",
        lines=[
            TransferLineCreate(
                item_id=100,
                source_location_id=1000,
                destination_location_id=2000,
                quantity=5,
            )
        ],
    )
    assert payload.lines[0].quantity == 5
    assert payload.source_warehouse_id != payload.destination_warehouse_id
