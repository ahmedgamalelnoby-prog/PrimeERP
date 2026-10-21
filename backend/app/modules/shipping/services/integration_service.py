"""Shipping provider execution and ERP transaction bridge."""
from datetime import date
from typing import Any
from sqlalchemy.orm import Session
from app.modules.identity.models import User
from app.modules.transactions.schemas import TransactionCreate
from app.modules.transactions.services.transaction_service import transaction_service
from ..models import Shipment, ShippingProvider
from ..connection_models import ShippingConnection
from ..connectors.bosta import BostaConnector
from ..connectors.aramex import AramexConnector
from ..connectors.registry import HttpShippingConnector


def connector_for(connection: ShippingConnection, provider: ShippingProvider):
    if provider.code.upper() == "BOSTA":
        if not connection.secret_ref: raise RuntimeError("Bosta connection requires secret_ref")
        return BostaConnector(connection.secret_ref, base_url=connection.base_url)
    if provider.code.upper() == "ARAMEX":
        refs = (connection.secret_ref or "").split(",")
        if len(refs) != 4: raise RuntimeError("Aramex secret_ref must contain account,username,password,pin environment variable references")
        return AramexConnector(refs[0].strip(), refs[1].strip(), refs[2].strip(), refs[3].strip(), base_url=connection.base_url)
    if not connection.base_url: raise RuntimeError("Shipping connection requires base_url for this provider")
    return HttpShippingConnector(connection.base_url, connection.secret_ref)


def create_shipping_transaction(db: Session, shipment: Shipment, user: User):
    if not shipment.company_id or not shipment.branch_id: return None
    return transaction_service.create_transaction(
        db=db,
        payload=TransactionCreate(
            company_id=shipment.company_id,
            branch_id=shipment.branch_id,
            transaction_type="shipment",
            source_module="shipping",
            source_entity="shipment",
            source_id=shipment.id,
            document_number=shipment.reference,
            reference_number=shipment.reference,
            external_reference=shipment.external_id,
            transaction_date=date.today(),
            metadata_json={"cod_amount": str(shipment.cod_amount or 0), "shipping_fee": str(shipment.shipping_fee or 0), "cod_fee": str(shipment.cod_fee or 0), "other_fee": str(shipment.other_fee or 0), "provider_id": shipment.provider_id},
        ),
        current_user=user,
    )


def normalize_provider_result(provider_code: str, result: dict[str, Any]) -> dict[str, Any]:
    data = result.get("data") if isinstance(result.get("data"), dict) else result
    tracking = data.get("trackingNumber") or data.get("tracking_number") or data.get("TrackingNumber")
    external_id = data.get("_id") or data.get("id") or data.get("ID")
    if isinstance(data.get("shipment"), dict):
        tracking = tracking or data["shipment"].get("trackingNumber")
        external_id = external_id or data["shipment"].get("id")
    return {"tracking_number": tracking, "external_id": external_id, "raw": result, "provider": provider_code}
