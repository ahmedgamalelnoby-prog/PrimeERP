"""Provider-neutral order orchestration.

Adapters normalize external orders; this service applies the same PrimeERP
commercial, inventory and accounting lifecycle regardless of provider.
"""
from __future__ import annotations
from datetime import date
from decimal import Decimal
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.commerce.models import BusinessPartner, SalesDocument, SalesLine
from app.modules.commerce.schemas import DocumentCreate, DocumentLineCreate
from app.modules.commerce.service import commerce_service
from app.modules.integrations.commerce_contracts import CanonicalOrder
from app.modules.integrations.commerce_registry import registry
from app.modules.integrations.models import IntegrationConnection, IntegrationMapping, IntegrationProductMapping
from app.modules.companies.models import Company
from app.modules.identity.models import User
from app.modules.commerce.payment_workflow import post_payment
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.shipping.models import Shipment, ShippingMethod, ShippingCarrier
from app.modules.shipping.integration import find_mapped_carrier, link_carrier

def _date(value: Any) -> date:
    if isinstance(value, date): return value
    text = str(value or "").strip()
    return date.fromisoformat(text[:10]) if text else date.today()

def _mapping(db: Session, *, company_id: int, connection_id: int, entity_type: str, external_id: str):
    return db.scalar(select(IntegrationMapping).where(
        IntegrationMapping.company_id == company_id, IntegrationMapping.connection_id == connection_id,
        IntegrationMapping.entity_type == entity_type, IntegrationMapping.external_id == str(external_id)))

def _customer(db: Session, *, company_id: int, connection_id: int, external_id: str | None, name: str | None = None) -> BusinessPartner:
    key = external_id or "guest"
    mapped = _mapping(db, company_id=company_id, connection_id=connection_id, entity_type="commerce_customer", external_id=key)
    if mapped:
        partner = db.scalar(select(BusinessPartner).where(BusinessPartner.id == mapped.local_id, BusinessPartner.company_id == company_id))
        if partner:
            if name: partner.name = name[:200]
            return partner
    code = f"COM-{connection_id}-{key}"[:50]
    partner = db.scalar(select(BusinessPartner).where(BusinessPartner.company_id == company_id, BusinessPartner.code == code))
    if partner is None:
        partner = BusinessPartner(company_id=company_id, code=code, name=(name or f"Commerce Customer {key}")[:200], partner_type="customer")
        db.add(partner); db.flush()
    if mapped: mapped.local_id = partner.id
    else:
        db.add(IntegrationMapping(company_id=company_id, connection_id=connection_id, entity_type="commerce_customer", external_id=key, local_id=partner.id))
        db.flush()
    return partner

def _product_mapping(db: Session, *, company_id: int, connection_id: int, line) -> IntegrationProductMapping:
    candidates = []
    if line.variant_external_id:
        candidates = list(db.scalars(select(IntegrationProductMapping).where(
            IntegrationProductMapping.company_id == company_id, IntegrationProductMapping.connection_id == connection_id,
            IntegrationProductMapping.entity_type == "variant", IntegrationProductMapping.external_id == str(line.variant_external_id),
            IntegrationProductMapping.sync_status == "active")).all())
    if not candidates and line.item_external_id:
        candidates = list(db.scalars(select(IntegrationProductMapping).where(
            IntegrationProductMapping.company_id == company_id, IntegrationProductMapping.connection_id == connection_id,
            IntegrationProductMapping.entity_type == "product", IntegrationProductMapping.external_id == str(line.item_external_id),
            IntegrationProductMapping.sync_status == "active")).all())
    if not candidates and line.sku:
        candidates = list(db.scalars(select(IntegrationProductMapping).where(
            IntegrationProductMapping.company_id == company_id, IntegrationProductMapping.connection_id == connection_id,
            IntegrationProductMapping.entity_type == "product", IntegrationProductMapping.external_sku == str(line.sku),
            IntegrationProductMapping.sync_status == "active")).all())
    if len(candidates) != 1:
        raise ValueError(f"Commerce line '{line.external_line_id}' has no unique active Product mapping")
    if candidates[0].catalog_product_id is None:
        raise ValueError(f"Commerce line '{line.external_line_id}' is mapped without a commercial Product identity")
    return candidates[0]

class CommerceOrderOrchestrator:
    def ingest(self, db: Session, *, connection_id: int, payload: dict[str, Any], user_id: int | None = None, fulfill: bool = True) -> dict[str, Any]:
        connection = db.scalar(select(IntegrationConnection).where(IntegrationConnection.id == connection_id, IntegrationConnection.is_active.is_(True)))
        if connection is None: raise ValueError("Commerce integration connection not found or inactive")
        adapter = registry.get(connection.provider)
        canonical: CanonicalOrder = adapter.normalize_order(db, connection, payload)
        if canonical.connection_id != connection.id or canonical.platform != connection.provider:
            raise ValueError("Adapter returned an order for a different connection/provider")
        existing = _mapping(db, company_id=connection.company_id, connection_id=connection.id, entity_type="commerce_order", external_id=canonical.external_order_id)
        if existing:
            document = db.scalar(select(SalesDocument).where(SalesDocument.id == existing.local_id, SalesDocument.company_id == connection.company_id))
            if document: return {"status": "already_processed", "sales_document_id": document.id, "external_order_id": canonical.external_order_id}
        if not canonical.lines: raise ValueError("Commerce order must contain at least one product line")
        resolved = [_product_mapping(db, company_id=connection.company_id, connection_id=connection.id, line=line) for line in canonical.lines]
        partner = _customer(db, company_id=connection.company_id, connection_id=connection.id, external_id=canonical.customer_external_id, name=canonical.metadata.get("customer_name"))
        warehouse_id = canonical.metadata.get("warehouse_id")
        if warehouse_id is None: raise ValueError("Canonical order metadata must contain warehouse_id before fulfillment")
        lines = []
        for line, mapping in zip(canonical.lines, resolved):
            gross = Decimal(line.quantity) * Decimal(line.unit_price)
            discount_percent = (Decimal(line.discount) / gross * 100) if gross else Decimal("0")
            tax_ids = list(line.metadata.get("tax_rate_ids") or []) if isinstance(line.metadata, dict) else []
            lines.append(DocumentLineCreate(item_id=mapping.product_id, variant_id=mapping.variant_id, tax_rate_ids=tax_ids,
                description=(line.metadata.get("name") if isinstance(line.metadata, dict) else None), quantity=Decimal(line.quantity),
                unit_price=Decimal(line.unit_price), discount_percent=discount_percent, tax_percent=Decimal("0")))
        document = commerce_service.create_document(db, DocumentCreate(company_id=connection.company_id, partner_id=partner.id,
            document_type="invoice", number=f"{canonical.platform.upper()}-{canonical.external_order_id}"[:60], document_date=_date(canonical.order_date),
            warehouse_id=int(warehouse_id), notes=f"Imported from {canonical.platform} order {canonical.external_order_id}", lines=lines))
        for sales_line, mapping in zip(document.lines, resolved): sales_line.catalog_product_id = mapping.catalog_product_id
        db.flush()
        if user_id is None:
            company = db.scalar(select(Company).where(Company.id == connection.company_id))
            if company is None or company.tenant_id is None:
                raise ValueError("Company tenant context is missing")
            user = db.scalar(select(User).where(User.tenant_id == company.tenant_id, User.is_active.is_(True)).order_by(User.id))
            if user is None:
                raise ValueError("No active tenant user is available for ERP posting")
            user_id = user.id
        commerce_service.confirm(db, connection.company_id, document.id, "sale", user_id=user_id)
        payment_ids = []
        for payment in canonical.payments:
            paid_amount = Decimal(payment.paid_amount or 0)
            if paid_amount <= 0:
                continue
            idempotency = f"commerce:{canonical.platform}:{connection.id}:{canonical.external_order_id}:payment:{payment.method}"
            existing_payment = db.scalar(select(__import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment).where(
                __import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.company_id == connection.company_id,
                __import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.document_id == document.id,
                __import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.document_kind == "sale",
                __import__("app.modules.commerce.models", fromlist=["CommercePayment"]).CommercePayment.idempotency_key == idempotency,
            ))
            if existing_payment:
                payment_ids.append(existing_payment.id)
                continue
            _, posted_payment = post_payment(
                db, company_id=connection.company_id, document_kind="sale", document_id=document.id,
                amount=min(paid_amount, Decimal(document.total) - Decimal(document.paid_total)),
                payment_date=document.document_date, method=payment.method, wht_amount=Decimal("0"),
                reference=str(payment.metadata.get("reference") or canonical.external_order_id)[:100],
                notes=f"Imported from {canonical.platform} order {canonical.external_order_id}",
                idempotency_key=idempotency,
            )
            commerce_accounting_service.post_payment(db, posted_payment, document, user_id)
            payment_ids.append(posted_payment.id)

        shipment_ids = []
        for shipment in canonical.shipments:
            if not shipment.external_shipment_id:
                continue
            carrier = None
            if shipment.external_carrier_id:
                carrier = find_mapped_carrier(
                    db, company_id=connection.company_id, connection_id=connection.id,
                    external_carrier_id=shipment.external_carrier_id,
                )
            if carrier is None and shipment.carrier_name:
                carrier = db.scalar(select(ShippingCarrier).where(
                    ShippingCarrier.company_id == connection.company_id,
                    ShippingCarrier.name.ilike(str(shipment.carrier_name).strip()),
                    ShippingCarrier.is_active.is_(True),
                ).order_by(ShippingCarrier.id))
                if carrier is not None and shipment.external_carrier_id:
                    link_carrier(
                        db, company_id=connection.company_id, connection_id=connection.id,
                        external_carrier_id=shipment.external_carrier_id, carrier_id=carrier.id,
                    )
            if carrier is None:
                if shipment.external_carrier_id or shipment.carrier_name:
                    raise ValueError(f"Commerce shipment '{shipment.external_shipment_id}' has no mapped PrimeERP shipping carrier")
                continue
            method_payment = "cod" if shipment.payment_method == "cod" else "prepaid"
            method = db.scalar(select(ShippingMethod).where(
                ShippingMethod.carrier_id == carrier.id,
                ShippingMethod.payment_method.in_((method_payment, "mixed")),
            ).order_by(ShippingMethod.id))
            if method is None:
                raise ValueError(f"Shipping carrier '{carrier.name}' has no compatible {method_payment} shipping method")
            tracking = shipment.tracking_number or shipment.external_shipment_id
            existing_shipment = db.scalar(select(Shipment).where(
                Shipment.company_id == connection.company_id,
                Shipment.sales_document_id == document.id,
                Shipment.tracking_no == tracking,
            ))
            if existing_shipment:
                shipment_ids.append(existing_shipment.id)
                continue
            shipping_row = Shipment(
                company_id=connection.company_id, carrier_id=carrier.id, method_id=method.id,
                sales_document_id=document.id, tracking_no=tracking,
                order_date=document.document_date, shipment_date=document.document_date,
                order_value=Decimal(document.total), cod_amount=Decimal(shipment.cod_amount or 0),
                card_amount=Decimal(document.total) - Decimal(shipment.cod_amount or 0),
                status=shipment.status, shipping_fee=Decimal(shipment.shipping_fee or 0),
                customer_shipping_fee=Decimal(shipment.customer_shipping_fee or 0),
                customer_name=str(canonical.metadata.get("customer_name") or document.partner.name)[:200],
                notes=f"{canonical.platform} shipment {shipment.external_shipment_id}",
            )
            db.add(shipping_row); db.flush()
            shipment_ids.append(shipping_row.id)

        delivery_id = None
        if fulfill:
            delivery = SalesDocument(company_id=document.company_id, partner_id=document.partner_id, document_type="delivery",
                number=f"{canonical.platform.upper()}-DEL-{canonical.external_order_id}"[:60], document_date=document.document_date,
                warehouse_id=document.warehouse_id, notes=f"Fulfillment for {canonical.platform} order {canonical.external_order_id}",
                subtotal=document.subtotal, tax_total=Decimal("0"), discount_total=document.discount_total, total=document.subtotal)
            for line in document.lines:
                delivery.lines.append(SalesLine(item_id=line.item_id, catalog_product_id=line.catalog_product_id, variant_id=line.variant_id,
                    tax_rate_id=None, tax_rate_ids=[], description=line.description, quantity=line.quantity, unit_price=line.unit_price,
                    discount_percent=line.discount_percent, tax_percent=Decimal("0"), line_total=(Decimal(line.quantity)*Decimal(line.unit_price)*
                    (Decimal("100")-Decimal(line.discount_percent or 0))/Decimal("100"))))
            db.add(delivery); db.flush()
            commerce_service.post_inventory(db, company_id=document.company_id, document_id=delivery.id, kind="sale", user_id=user_id)
            delivery_id = delivery.id
        db.add(IntegrationMapping(company_id=connection.company_id, connection_id=connection.id, entity_type="commerce_order",
            external_id=canonical.external_order_id, local_id=document.id))
        db.commit()
        return {"status":"processed","sales_document_id":document.id,"delivery_document_id":delivery_id,"payment_ids":payment_ids,"shipment_ids":shipment_ids,"external_order_id":canonical.external_order_id,
                "revenue":str(document.subtotal),"tax":str(document.tax_total)}

commerce_order_orchestrator = CommerceOrderOrchestrator()
