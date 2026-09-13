from __future__ import annotations
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.modules.accounting.models import TaxRate
from app.modules.commerce.accounting_service import commerce_accounting_service
from app.modules.commerce.models import BusinessPartner, SalesDocument, SalesLine
from app.modules.commerce.payment_workflow import post_payment
from app.modules.companies.models import Company
from app.modules.identity.models import User
from app.modules.integrations.models import IntegrationMapping
from app.modules.integrations.salla_models import SallaCustomer, SallaOrder, SallaOrderItem, SallaProduct
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.uom.models import UnitOfMeasure

class SallaERPExecutionError(ValueError): pass

def _d(value) -> Decimal: return Decimal(str(value or 0))

def _mapping(db, company_id, connection_id, entity_type, external_id):
    return db.scalar(select(IntegrationMapping).where(IntegrationMapping.company_id == company_id, IntegrationMapping.connection_id == connection_id, IntegrationMapping.entity_type == entity_type, IntegrationMapping.external_id == str(external_id)))

def _set_mapping(db, company_id, connection_id, entity_type, external_id, local_id):
    obj = _mapping(db, company_id, connection_id, entity_type, external_id)
    if obj: obj.local_id = local_id; return obj
    obj = IntegrationMapping(company_id=company_id, connection_id=connection_id, entity_type=entity_type, external_id=str(external_id), local_id=local_id)
    db.add(obj); db.flush(); return obj

def _system_user_id(db, company_id):
    company = db.scalar(select(Company).where(Company.id == company_id))
    if not company or company.tenant_id is None: raise SallaERPExecutionError("Company tenant context is missing")
    user = db.scalar(select(User).where(User.tenant_id == company.tenant_id, User.is_active.is_(True)).order_by(User.id))
    if not user: raise SallaERPExecutionError("No active tenant user is available for ERP posting")
    return user.id

def _uom(db, company_id):
    obj = db.scalar(select(UnitOfMeasure).where(UnitOfMeasure.company_id == company_id, UnitOfMeasure.code == "unit", UnitOfMeasure.is_active.is_(True)))
    if obj: return obj
    obj = db.scalar(select(UnitOfMeasure).where(UnitOfMeasure.company_id == company_id, UnitOfMeasure.is_active.is_(True)).order_by(UnitOfMeasure.id))
    if not obj: raise SallaERPExecutionError("No active UOM is configured for the company")
    return obj

def _customer(db, order, customer):
    external_id = order.customer_id or f"guest-{order.external_id}"
    mapped = _mapping(db, order.company_id, order.connection_id, "salla_customer", external_id)
    if mapped:
        obj = db.scalar(select(BusinessPartner).where(BusinessPartner.id == mapped.local_id, BusinessPartner.company_id == order.company_id))
        if obj:
            if customer:
                obj.name = " ".join(x for x in [customer.first_name, customer.last_name] if x) or obj.name; obj.phone = customer.mobile or obj.phone; obj.email = customer.email or obj.email
            return obj
    name = " ".join(x for x in [customer.first_name if customer else None, customer.last_name if customer else None] if x) or f"Salla Customer {external_id}"
    code = f"SALLA-{external_id}"[:50]
    obj = db.scalar(select(BusinessPartner).where(BusinessPartner.company_id == order.company_id, BusinessPartner.code == code))
    if not obj:
        obj = BusinessPartner(company_id=order.company_id, code=code, name=name, partner_type="customer", phone=customer.mobile if customer else None, email=customer.email if customer else None); db.add(obj); db.flush()
    _set_mapping(db, order.company_id, order.connection_id, "salla_customer", external_id, obj.id); return obj

def _tax_id_for_item(db, company_id, item):
    base = _d(item.subtotal) - _d(item.discount); tax = _d(item.tax)
    if base <= 0 or tax <= 0: return None
    rate = (tax / base * Decimal("100")).quantize(Decimal("0.0001"))
    taxes = db.scalars(select(TaxRate).where(TaxRate.company_id == company_id, TaxRate.is_active.is_(True), TaxRate.is_withholding.is_(False))).all()
    matches = [t for t in taxes if abs(Decimal(t.rate) - rate) <= Decimal("0.02")]
    if not matches: raise SallaERPExecutionError(f"No active ERP Tax Master rate matches Salla tax rate {rate}% for item {item.external_id}")
    return min(matches, key=lambda t: abs(Decimal(t.rate) - rate)).id

def _product(db, order, item):
    external = item.variant_external_id or item.product_external_id or item.sku
    if not external: raise SallaERPExecutionError(f"Salla order item {item.external_id} has no product/SKU identifier")
    mapped = _mapping(db, order.company_id, order.connection_id, "salla_product", external)
    if mapped:
        obj = db.scalar(select(InventoryItem).where(InventoryItem.id == mapped.local_id, InventoryItem.company_id == order.company_id))
        if obj: return obj
    sku = (item.sku or f"SALLA-{external}")[:80]
    obj = db.scalar(select(InventoryItem).where(InventoryItem.company_id == order.company_id, InventoryItem.sku == sku))
    tax_id = _tax_id_for_item(db, order.company_id, item)
    if not obj:
        uom = _uom(db, order.company_id); raw = db.scalar(select(SallaProduct).where(SallaProduct.connection_id == order.connection_id, SallaProduct.external_id == (item.product_external_id or external))); name = item.name or (raw.name if raw else None) or sku
        obj = InventoryItem(company_id=order.company_id, sku=sku, name_ar=name[:200], name_en=name[:200], item_type="stockable", uom=uom.code, uom_id=uom.id, sales_tax_ids=[tax_id] if tax_id else [], purchase_tax_ids=[], standard_cost=_d(item.cost_price), sales_price=_d(item.price), purchase_price=_d(item.cost_price), is_active=True); db.add(obj); db.flush()
    elif tax_id and not obj.sales_tax_ids: obj.sales_tax_ids = [tax_id]
    _set_mapping(db, order.company_id, order.connection_id, "salla_product", external, obj.id); return obj

def _warehouse(db, company_id):
    return db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.company_id == company_id, InventoryWarehouse.is_active.is_(True)).order_by(InventoryWarehouse.is_central.desc(), InventoryWarehouse.id))

def _document(db, order, partner, items: Iterable[SallaOrderItem], warehouse_id):
    mapped = _mapping(db, order.company_id, order.connection_id, "salla_order", order.external_id)
    if mapped:
        existing = db.scalar(select(SalesDocument).where(SalesDocument.id == mapped.local_id, SalesDocument.company_id == order.company_id))
        if existing: return existing
    number = f"SALLA-{order.reference_id or order.external_id}"[:60]
    existing = db.scalar(select(SalesDocument).where(SalesDocument.company_id == order.company_id, SalesDocument.number == number))
    if existing: _set_mapping(db, order.company_id, order.connection_id, "salla_order", order.external_id, existing.id); return existing
    document = SalesDocument(company_id=order.company_id, partner_id=partner.id, document_type="invoice", number=number, document_date=(order.created_at_salla.date() if order.created_at_salla else date.today()), warehouse_id=warehouse_id, notes=f"Imported from Salla order {order.external_id}")
    subtotal = Decimal("0"); tax_total = Decimal("0"); discount_total = Decimal("0")
    for s_item in items:
        if _d(s_item.quantity) <= 0: continue
        product = _product(db, order, s_item); quantity = _d(s_item.quantity); price = _d(s_item.price); gross = quantity * price; discount = _d(s_item.discount); net = max(gross - discount, Decimal("0")); tax_id = _tax_id_for_item(db, order.company_id, s_item); tax_amount = _d(s_item.tax)
        document.lines.append(SalesLine(item_id=product.id, tax_rate_id=tax_id, tax_rate_ids=[tax_id] if tax_id else [], description=s_item.name, quantity=quantity, unit_price=price, discount_percent=((discount / gross * Decimal("100")) if gross else Decimal("0")), tax_percent=Decimal("0"), line_total=net + tax_amount))
        subtotal += net; tax_total += tax_amount; discount_total += discount
    shipping = _d(order.shipping)
    if shipping:
        shipping_item = db.scalar(select(InventoryItem).where(InventoryItem.company_id == order.company_id, InventoryItem.sku == "SALLA-SHIPPING"))
        if not shipping_item:
            uom = _uom(db, order.company_id); shipping_item = InventoryItem(company_id=order.company_id, sku="SALLA-SHIPPING", name_ar="Salla Shipping", name_en="Salla Shipping", item_type="service", uom=uom.code, uom_id=uom.id, sales_price=shipping, purchase_price=0, standard_cost=0, is_active=True); db.add(shipping_item); db.flush()
        document.lines.append(SalesLine(item_id=shipping_item.id, description="Salla shipping", quantity=Decimal("1"), unit_price=shipping, discount_percent=0, tax_percent=0, tax_rate_ids=[], line_total=shipping)); subtotal += shipping
    document.subtotal = subtotal; document.tax_total = tax_total; document.discount_total = discount_total; document.total = subtotal + tax_total
    if order.total is not None and abs(Decimal(document.total) - Decimal(order.total)) > Decimal("0.02"): raise SallaERPExecutionError(f"Salla order {order.external_id} total mismatch: ERP candidate {document.total} vs Salla {order.total}")
    db.add(document); db.flush(); _set_mapping(db, order.company_id, order.connection_id, "salla_order", order.external_id, document.id); return document

def _payment(db, order, document, user_id):
    if str(order.payment_status or "").lower() not in {"paid", "completed", "success", "successful"}: return None
    amount = _d(order.total)
    if amount <= 0 or document.paid_total >= amount: return None
    methods = order.payment_methods or []; raw_method = "salla"; reference = order.reference_id or order.external_id
    if methods and isinstance(methods[0], dict): raw_method = str(methods[0].get("payment_method") or methods[0].get("name") or "salla"); reference = str(methods[0].get("transaction_reference") or reference)[:100]
    elif methods and isinstance(methods[0], str): raw_method = methods[0]
    method_key = raw_method.lower().replace("-", "_").replace(" ", "_")
    if method_key in {"cash", "cash_on_delivery", "cod"}: method = "cod" if method_key != "cash" else "cash"
    elif method_key in {"bank", "bank_transfer", "banktransfer"}: method = "bank_transfer"
    elif method_key in {"credit_card", "creditcard", "card", "mada", "apple_pay", "stc_pay", "visa", "mastercard"}: method = "card"
    elif method_key in {"wallet", "digital_wallet"}: method = "wallet"
    elif method_key == "cheque": method = "cheque"
    else: method = "other"
    _, payment = post_payment(db, company_id=order.company_id, document_kind="sale", document_id=document.id, amount=amount - _d(document.paid_total), payment_date=document.document_date, method=method, wht_amount=Decimal("0"), reference=reference, notes=f"Salla order {order.external_id}", idempotency_key=f"salla:{order.connection_id}:{order.external_id}:payment")
    commerce_accounting_service.post_payment(db, payment, document, user_id); return payment

def execute_salla_order(db, order, user_id=None):
    if order.erp_status == "processed" and order.erp_entity_id: return {"status": "already_processed", "sales_document_id": order.erp_entity_id}
    try:
        if user_id is None: user_id = _system_user_id(db, order.company_id)
        customer = db.scalar(select(SallaCustomer).where(SallaCustomer.connection_id == order.connection_id, SallaCustomer.external_id == order.customer_id)) if order.customer_id else None
        partner = _customer(db, order, customer); items = list(db.scalars(select(SallaOrderItem).where(SallaOrderItem.order_id == order.id).order_by(SallaOrderItem.id)).all())
        if not items: raise SallaERPExecutionError(f"Salla order {order.external_id} has no normalized order items")
        warehouse = _warehouse(db, order.company_id); document = _document(db, order, partner, items, warehouse.id if warehouse else None)
        if document.status == "draft": document.status = "confirmed"; db.flush()
        commerce_accounting_service.post_sales_invoice(db, document, user_id); payment = _payment(db, order, document, user_id)
        order.erp_status = "processed"; order.erp_entity_id = document.id; order.erp_error = None; order.erp_synced_at = datetime.now(timezone.utc); db.flush()
        return {"status": "processed", "sales_document_id": document.id, "payment_id": payment.id if payment else None}
    except Exception as exc:
        order.erp_status = "failed"; order.erp_error = str(exc)[:4000]; order.erp_synced_at = datetime.now(timezone.utc); db.flush(); raise

def execute_pending_salla_orders(db, company_id, user_id=None, limit=50):
    orders = db.scalars(select(SallaOrder).where(SallaOrder.company_id == company_id, SallaOrder.erp_status.in_(["pending", "failed"])).order_by(SallaOrder.id).limit(limit).with_for_update()).all(); processed = failed = 0; errors = []
    for order in orders:
        try: execute_salla_order(db, order, user_id=user_id); db.commit(); processed += 1
        except Exception as exc: db.rollback(); failed += 1; errors.append({"order_id": order.external_id, "error": str(exc)[:500]})
    return {"processed": processed, "failed": failed, "errors": errors}
