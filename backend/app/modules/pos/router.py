from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.catalog.models import Menu, MenuItem, ProductPrice
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
from app.modules.commerce.models import SalesDocument, SalesLine
from app.modules.commerce.schemas import DocumentCreate, DocumentLineCreate, PaymentCreate
from app.modules.commerce.service import commerce_service
from app.modules.commerce.sales_return_schemas import SalesReturnCreate
from app.modules.commerce.sales_return_service import sales_return_service
from app.modules.commerce.payment_workflow import reverse_payment
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.inventory.items.models import InventoryItem
from app.modules.inventory.warehouses.models import InventoryWarehouse
from app.modules.inventory.locations.models import InventoryLocation
from app.modules.inventory.stock_moves.schemas import StockMoveCreate
from app.modules.inventory.stock_moves.service import inventory_stock_move_service
from app.modules.inventory.reservations.schemas import ReservationCreate
from app.modules.inventory.reservations.service import inventory_reservation_service
from app.modules.inventory.transfers.schemas import TransferCreate
from app.modules.inventory.transfers.service import inventory_transfer_service
from app.modules.commerce.payment_workflow import post_payment, reverse_payment
from app.modules.jurisdiction.commerce_guard import capture_document_tax_snapshot, validate_document_tax_snapshot
from app.modules.pos.completion_models import POSModifierGroup, POSModifierOption, POSPromotion, POSPromotionUse
from app.modules.restaurant.models import (
    Floor, RestaurantTable, OrderType,
    PreparationStation,
    PosMenuItemRoute,
    PosOrderLineRoute,
    PosOutlet,
    PosOutletStation,
    PosTerminal,
    PosTerminalMenu,
)

router = APIRouter(prefix="/pos", tags=["POS"], dependencies=[Depends(require_permission("commerce.access"))])


class OutletCreate(BaseModel):
    company_id: int = Field(gt=0)
    branch_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    outlet_type: str = Field(default="restaurant", min_length=2, max_length=30)
    warehouse_id: int | None = Field(default=None, gt=0)


class StationCreate(BaseModel):
    branch_id: int = Field(gt=0)
    outlet_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=30)
    station_type: str = Field(default="kitchen", min_length=2, max_length=50)
    is_kds_enabled: bool = True
    is_printer_enabled: bool = False
    printer_name: str | None = None


class TerminalCreate(BaseModel):
    company_id: int = Field(gt=0)
    branch_id: int = Field(gt=0)
    outlet_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=1, max_length=160)
    device_identifier: str | None = Field(default=None, max_length=160)


class OutletStationLink(BaseModel):
    outlet_id: int = Field(gt=0)
    station_id: int = Field(gt=0)


class TerminalMenuLink(BaseModel):
    terminal_id: int = Field(gt=0)
    menu_id: int = Field(gt=0)
    price_list_id: int | None = Field(default=None, gt=0)


class MenuItemRouteCreate(BaseModel):
    terminal_id: int = Field(gt=0)
    menu_item_id: int = Field(gt=0)
    station_id: int = Field(gt=0)


class CheckoutLine(BaseModel):
    menu_item_id: int | None = Field(default=None, gt=0)
    item_id: int | None = Field(default=None, gt=0)
    variant_id: int | None = Field(default=None, gt=0)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    discount_percent: Decimal = Field(default=0, ge=0, le=100)
    modifier_option_ids: list[int] = Field(default_factory=list)


class Checkout(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    number: str = Field(min_length=1, max_length=60)
    payment_date: date
    method: str = Field(min_length=1, max_length=30)
    terminal_id: int | None = Field(default=None, gt=0)
    lines: list[CheckoutLine] = Field(min_length=1)
    promotion_code: str | None = Field(default=None, max_length=80)


class SplitPayment(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str = Field(min_length=1, max_length=30)
    reference: str | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)

class SplitPaymentRequest(BaseModel):
    payments: list[SplitPayment] = Field(min_length=1)

class TableStatusUpdate(BaseModel):
    status: str = Field(pattern="^(available|occupied|reserved|cleaning|out_of_service)$")

class RouteStatusUpdate(BaseModel):
    status: str = Field(pattern="^(queued|preparing|ready|served|cancelled)$")
    notes: str | None = None


def _company(db: Session, company_id: int, user: User) -> Company:
    if user.tenant_id is None:
        raise HTTPException(403, "User is not assigned to a tenant")
    company = db.scalar(select(Company).where(
        Company.id == company_id,
        Company.tenant_id == user.tenant_id,
        Company.is_active.is_(True),
    ))
    if company is None:
        raise HTTPException(403, "Company is outside the current tenant")
    return company


def _branch(db: Session, company_id: int, branch_id: int):
    branch = db.scalar(select(Branch).where(
        Branch.id == branch_id,
        Branch.company_id == company_id,
        Branch.is_active.is_(True),
    ))
    if branch is None:
        raise HTTPException(422, "Branch does not belong to the company or is inactive")
    return branch


def _terminal(db: Session, company_id: int, terminal_id: int) -> PosTerminal:
    terminal = db.scalar(select(PosTerminal).where(
        PosTerminal.id == terminal_id,
        PosTerminal.company_id == company_id,
        PosTerminal.is_active.is_(True),
    ))
    if terminal is None:
        raise HTTPException(422, "POS terminal does not belong to the company or is inactive")
    return terminal

def _modifier_options(db: Session, company_id: int, option_ids: list[int]) -> list[POSModifierOption]:
    if not option_ids:
        return []
    if len(option_ids) != len(set(option_ids)):
        raise HTTPException(422, "Duplicate POS modifier options are not allowed")
    rows = list(db.execute(
        select(POSModifierOption, POSModifierGroup)
        .join(POSModifierGroup, POSModifierGroup.id == POSModifierOption.group_id)
        .where(
            POSModifierOption.id.in_(option_ids),
            POSModifierOption.is_active.is_(True),
            POSModifierGroup.company_id == company_id,
            POSModifierGroup.is_active.is_(True),
        )
    ).all())
    if len(rows) != len(option_ids):
        raise HTTPException(422, "One or more POS modifier options are invalid, inactive, or outside the company")
    counts = {}
    groups = {}
    for option, group in rows:
        counts[group.id] = counts.get(group.id, 0) + 1
        groups[group.id] = group
    for group_id, count in counts.items():
        group = groups[group_id]
        if count > int(group.max_select or 0):
            raise HTTPException(422, f"Modifier group {group.name} allows at most {group.max_select} selections")
    return [option for option, _group in rows]


@router.get("/sales")
def sales(
    company_id: int = Query(..., gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company(db, company_id, current_user)
    return commerce_service.list_documents(db, company_id, "sale", "invoice")


@router.get("/outlets")
def list_outlets(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    return list(db.scalars(select(PosOutlet).where(PosOutlet.company_id == company_id).order_by(PosOutlet.name)).all())


@router.post("/outlets", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_outlet(payload: OutletCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    _branch(db, payload.company_id, payload.branch_id)
    if payload.warehouse_id is not None:
        warehouse = db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.id == payload.warehouse_id, InventoryWarehouse.company_id == payload.company_id, InventoryWarehouse.is_active.is_(True)))
        if warehouse is None or warehouse.branch_id != payload.branch_id:
            raise HTTPException(422, "Outlet warehouse must belong to the same company and branch")
    if db.scalar(select(PosOutlet).where(PosOutlet.company_id == payload.company_id, PosOutlet.code == payload.code)):
        raise HTTPException(409, "Outlet code already exists")
    obj = PosOutlet(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/outlets/{outlet_id}/warehouse", dependencies=[Depends(require_permission("inventory.write"))])
def assign_outlet_warehouse(outlet_id: int, warehouse_id: int = Query(..., gt=0), company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    outlet = db.scalar(select(PosOutlet).where(PosOutlet.id == outlet_id, PosOutlet.company_id == company_id, PosOutlet.is_active.is_(True)).with_for_update())
    warehouse = db.scalar(select(InventoryWarehouse).where(InventoryWarehouse.id == warehouse_id, InventoryWarehouse.company_id == company_id, InventoryWarehouse.is_active.is_(True)))
    if outlet is None or warehouse is None or outlet.branch_id != warehouse.branch_id:
        raise HTTPException(422, "Outlet and warehouse must belong to the same company and branch")
    outlet.warehouse_id = warehouse.id
    db.commit()
    db.refresh(outlet)
    return outlet


@router.get("/warehouses")
def list_warehouses(company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    return list(db.scalars(select(InventoryWarehouse).where(InventoryWarehouse.company_id == company_id, InventoryWarehouse.is_active.is_(True)).order_by(InventoryWarehouse.is_central.desc(), InventoryWarehouse.name)).all())


@router.get("/stations")
def list_stations(company_id: int = Query(..., gt=0), outlet_id: int | None = Query(default=None, gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    q = select(PreparationStation).join(Branch, Branch.id == PreparationStation.branch_id).where(
        Branch.company_id == company_id,
        PreparationStation.is_active.is_(True),
    )
    if outlet_id:
        q = q.join(PosOutletStation, PosOutletStation.station_id == PreparationStation.id).where(
            PosOutletStation.outlet_id == outlet_id,
            PosOutletStation.is_active.is_(True),
        )
    return list(db.scalars(q.order_by(PreparationStation.display_order, PreparationStation.name)).all())


@router.post("/stations", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_station(payload: StationCreate, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    _branch(db, company_id, payload.branch_id)
    obj = PreparationStation(
        branch_id=payload.branch_id,
        name=payload.name,
        code=payload.code,
        station_type=payload.station_type,
        is_kds_enabled=payload.is_kds_enabled,
        is_printer_enabled=payload.is_printer_enabled,
        printer_name=payload.printer_name,
    )
    db.add(obj)
    db.flush()
    if payload.outlet_id:
        outlet = db.scalar(select(PosOutlet).where(PosOutlet.id == payload.outlet_id, PosOutlet.company_id == company_id, PosOutlet.branch_id == payload.branch_id, PosOutlet.is_active.is_(True)))
        if outlet is None:
            db.rollback()
            raise HTTPException(422, "Outlet does not belong to the branch/company")
        db.add(PosOutletStation(outlet_id=outlet.id, station_id=obj.id))
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/outlets/stations", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def link_outlet_station(payload: OutletStationLink, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    outlet = db.scalar(select(PosOutlet).where(PosOutlet.id == payload.outlet_id, PosOutlet.company_id == company_id, PosOutlet.is_active.is_(True)))
    station = db.scalar(select(PreparationStation).join(Branch, Branch.id == PreparationStation.branch_id).where(PreparationStation.id == payload.station_id, Branch.company_id == company_id, PreparationStation.is_active.is_(True)))
    if outlet is None or station is None or outlet.branch_id != station.branch_id:
        raise HTTPException(422, "Outlet and preparation station must belong to the same company and branch")
    obj = db.scalar(select(PosOutletStation).where(PosOutletStation.outlet_id == outlet.id, PosOutletStation.station_id == station.id))
    if obj is None:
        obj = PosOutletStation(outlet_id=outlet.id, station_id=station.id)
        db.add(obj)
    else:
        obj.is_active = True
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/terminals")
def list_terminals(company_id: int = Query(..., gt=0), outlet_id: int | None = Query(default=None, gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    q = select(PosTerminal).where(PosTerminal.company_id == company_id, PosTerminal.is_active.is_(True))
    if outlet_id:
        q = q.where(PosTerminal.outlet_id == outlet_id)
    return list(db.scalars(q.order_by(PosTerminal.name)).all())


@router.post("/terminals", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def create_terminal(payload: TerminalCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    _branch(db, payload.company_id, payload.branch_id)
    outlet = db.scalar(select(PosOutlet).where(PosOutlet.id == payload.outlet_id, PosOutlet.company_id == payload.company_id, PosOutlet.branch_id == payload.branch_id, PosOutlet.is_active.is_(True)))
    if outlet is None:
        raise HTTPException(422, "Outlet does not belong to the company/branch")
    if db.scalar(select(PosTerminal).where(PosTerminal.company_id == payload.company_id, PosTerminal.code == payload.code)):
        raise HTTPException(409, "Terminal code already exists")
    obj = PosTerminal(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/menus")
def terminal_menus(terminal_id: int = Query(..., gt=0), company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    terminal = _terminal(db, company_id, terminal_id)
    rows = db.execute(select(PosTerminalMenu, Menu).join(Menu, Menu.id == PosTerminalMenu.menu_id).where(
        PosTerminalMenu.terminal_id == terminal.id,
        PosTerminalMenu.is_active.is_(True),
        Menu.is_active.is_(True),
    )).all()
    return [{"id": link.id, "menu_id": menu.id, "name_ar": menu.name_ar, "name_en": menu.name_en, "price_list_id": link.price_list_id} for link, menu in rows]


@router.post("/terminals/menus", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def link_terminal_menu(payload: TerminalMenuLink, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    terminal = _terminal(db, company_id, payload.terminal_id)
    menu = db.scalar(select(Menu).where(Menu.id == payload.menu_id, Menu.company_id == company_id, Menu.is_active.is_(True)))
    if payload.price_list_id is not None and db.scalar(select(ProductPrice.id).where(ProductPrice.company_id == company_id, ProductPrice.price_list_id == payload.price_list_id).limit(1)) is None:
        raise HTTPException(422, "Price list does not belong to the company")
    if menu is None:
        raise HTTPException(422, "Menu does not belong to the company or is inactive")
    if menu.branch_id is not None and menu.branch_id != terminal.branch_id:
        raise HTTPException(422, "Menu belongs to another branch")
    obj = db.scalar(select(PosTerminalMenu).where(PosTerminalMenu.terminal_id == terminal.id, PosTerminalMenu.menu_id == menu.id))
    if obj is None:
        obj = PosTerminalMenu(terminal_id=terminal.id, menu_id=menu.id, price_list_id=payload.price_list_id)
        db.add(obj)
    else:
        obj.price_list_id = payload.price_list_id
        obj.is_active = True
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/menu-routes", status_code=201, dependencies=[Depends(require_permission("commerce.write"))])
def route_menu_item(payload: MenuItemRouteCreate, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    terminal = _terminal(db, company_id, payload.terminal_id)
    item = db.scalar(select(MenuItem).join(Menu, Menu.id == MenuItem.menu_id).where(
        MenuItem.id == payload.menu_item_id,
        Menu.company_id == company_id,
        MenuItem.is_available.is_(True),
    ))
    station = db.scalar(select(PreparationStation).join(Branch, Branch.id == PreparationStation.branch_id).where(
        PreparationStation.id == payload.station_id,
        Branch.company_id == company_id,
        PreparationStation.is_active.is_(True),
    ))
    terminal_menu = db.scalar(select(PosTerminalMenu).where(
        PosTerminalMenu.terminal_id == terminal.id,
        PosTerminalMenu.menu_id == MenuItem.menu_id,
        PosTerminalMenu.is_active.is_(True),
    ))
    allowed_station = db.scalar(select(PosOutletStation).where(
        PosOutletStation.outlet_id == terminal.outlet_id,
        PosOutletStation.station_id == payload.station_id,
        PosOutletStation.is_active.is_(True),
    ))
    if item is None or station is None or terminal_menu is None or allowed_station is None:
        raise HTTPException(422, "Menu item, terminal menu, station, and outlet/station link must all be valid")
    obj = db.scalar(select(PosMenuItemRoute).where(PosMenuItemRoute.terminal_id == terminal.id, PosMenuItemRoute.menu_item_id == item.id))
    if obj is None:
        obj = PosMenuItemRoute(terminal_id=terminal.id, menu_item_id=item.id, station_id=station.id)
        db.add(obj)
    else:
        obj.station_id = station.id
        obj.is_active = True
    db.commit()
    db.refresh(obj)
    return obj


def _active_recipe(db: Session, company_id: int, item_id: int, variant_id: int | None):
    q = select(Recipe).where(Recipe.company_id == company_id, Recipe.product_id == item_id, Recipe.is_active.is_(True))
    if variant_id is not None:
        q = q.where(Recipe.variant_id == variant_id)
    else:
        q = q.where(Recipe.variant_id.is_(None))
    return db.scalar(q.order_by(Recipe.version.desc()))


def _expand_recipe(db: Session, company_id: int, item_id: int, variant_id: int | None, quantity: Decimal, visited: set[tuple[int, int | None]] | None = None):
    visited = set(visited or ())
    key = (item_id, variant_id)
    if key in visited:
        raise HTTPException(409, "Recursive POS recipe detected")
    recipe = _active_recipe(db, company_id, item_id, variant_id)
    if recipe is None:
        return [(item_id, variant_id, quantity)]
    visited.add(key)
    factor = Decimal(quantity) / Decimal(recipe.yield_quantity or 1)
    result = []
    for line in recipe.lines:
        component = line.ingredient_item_id or line.ingredient_product_id
        qty = Decimal(line.quantity) * factor * (Decimal("1") + Decimal(line.waste_percentage or 0) / Decimal("100"))
        nested_variant = getattr(line, "ingredient_variant_id", None)
        nested = _active_recipe(db, company_id, component, nested_variant)
        if nested:
            result.extend(_expand_recipe(db, company_id, component, nested_variant, qty, visited))
        else:
            result.append((component, nested_variant, qty))
    visited.remove(key)
    return result


def _post_recipe_consumption(db: Session, *, company_id: int, tenant_id: int, user_id: int, sale_id: int, sale_line: SalesLine, source_location_id: int, quantity: Decimal, reference: str):
    components = _expand_recipe(db, company_id, sale_line.item_id, sale_line.variant_id, quantity)
    for idx, (item_id, variant_id, qty) in enumerate(components, start=1):
        source_id = f"pos:{sale_id}:line:{sale_line.id}:recipe:{idx}:{item_id}:{variant_id or 0}"
        existing = db.scalar(select(__import__("app.modules.inventory.stock_moves.models", fromlist=["InventoryStockMove"]).InventoryStockMove).where(
            __import__("app.modules.inventory.stock_moves.models", fromlist=["InventoryStockMove"]).InventoryStockMove.company_id == company_id,
            __import__("app.modules.inventory.stock_moves.models", fromlist=["InventoryStockMove"]).InventoryStockMove.source_module == "pos",
            __import__("app.modules.inventory.stock_moves.models", fromlist=["InventoryStockMove"]).InventoryStockMove.source_entity == "recipe_consumption",
            __import__("app.modules.inventory.stock_moves.models", fromlist=["InventoryStockMove"]).InventoryStockMove.source_id == source_id,
        ))
        if existing:
            continue
        reservation = inventory_reservation_service.reserve(db, ReservationCreate(company_id=company_id, item_id=item_id, variant_id=variant_id, location_id=source_location_id, quantity=qty, source_module="pos", source_entity="recipe_consumption", source_id=source_id, reference=reference, notes=f"POS recipe reservation for sale {sale_id}, line {sale_line.id}"))
        move = inventory_stock_move_service.create_draft(db, StockMoveCreate(
            company_id=company_id, item_id=item_id, variant_id=variant_id,
            source_location_id=source_location_id, destination_location_id=None,
            quantity=qty, unit_cost=0, movement_type="issue", reference=reference,
            source_module="pos", source_entity="recipe_consumption", source_id=source_id,
            reservation_id=reservation.id,
            notes=f"POS recipe consumption for sale {sale_id}, line {sale_line.id}",
        ))
        inventory_stock_move_service.post(db, tenant_id=tenant_id, company_id=company_id, move_id=move.id, user_id=user_id)


def _menu_price(db: Session, company_id: int, menu_item: MenuItem, price_list_id: int | None, quantity: Decimal) -> Decimal:
    if menu_item.sale_price_override is not None:
        return Decimal(menu_item.sale_price_override)
    price_list_id = price_list_id or menu_item.price_list_id
    if price_list_id:
        price = db.scalar(select(ProductPrice).where(
            ProductPrice.company_id == company_id,
            ProductPrice.price_list_id == price_list_id,
            ProductPrice.product_id == menu_item.product_id,
            ProductPrice.is_active.is_(True),
            ProductPrice.min_quantity <= quantity,
        ).order_by(ProductPrice.min_quantity.desc(), ProductPrice.valid_from.desc()))
        if price is not None:
            return Decimal(price.sale_price)
    item = db.get(InventoryItem, menu_item.product_id)
    if item is None:
        raise HTTPException(422, "Menu item product no longer exists")
    return Decimal(item.sales_price or 0)


@router.post("/checkout", dependencies=[Depends(require_permission("commerce.payment"))])
def checkout(payload: Checkout, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    terminal = _terminal(db, payload.company_id, payload.terminal_id) if payload.terminal_id else None
    if terminal is not None:
        outlet = db.get(PosOutlet, terminal.outlet_id)
        if outlet is None or outlet.warehouse_id is None:
            raise HTTPException(422, "The POS outlet must have a consumption warehouse before selling")
        if payload.warehouse_id != outlet.warehouse_id:
            raise HTTPException(422, "POS consumption warehouse must match the terminal outlet warehouse")
    lines: list[DocumentLineCreate] = []
    routes: list[int | None] = []
    pre_discount_subtotal = sum((Decimal(str(x.unit_price or 0)) * Decimal(x.quantity) for x in payload.lines), Decimal("0"))
    promotion_percent = Decimal("0")
    if payload.promotion_code:
        promotion = db.scalar(select(POSPromotion).where(POSPromotion.company_id == payload.company_id, POSPromotion.code == payload.promotion_code, POSPromotion.is_active.is_(True)))
        if promotion is None:
            raise HTTPException(404, "Promotion not found")
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if (promotion.valid_from and now < promotion.valid_from) or (promotion.valid_to and now > promotion.valid_to):
            raise HTTPException(409, "Promotion is outside its validity window")
        promotion_percent = Decimal(promotion.discount_percent or 0)
        if promotion.max_discount is not None and pre_discount_subtotal > 0:
            promotion_percent = min(promotion_percent, Decimal(promotion.max_discount) * Decimal("100") / pre_discount_subtotal)
    for line in payload.lines:
        if line.menu_item_id:
            if terminal is None:
                raise HTTPException(422, "terminal_id is required when selling from a menu")
            menu_item = db.scalar(select(MenuItem).join(Menu, Menu.id == MenuItem.menu_id).where(
                MenuItem.id == line.menu_item_id,
                Menu.company_id == payload.company_id,
                MenuItem.is_available.is_(True),
            ))
            if menu_item is None:
                raise HTTPException(422, "Menu item does not exist or is unavailable")
            terminal_menu = db.scalar(select(PosTerminalMenu).where(
                PosTerminalMenu.terminal_id == terminal.id,
                PosTerminalMenu.menu_id == menu_item.menu_id,
                PosTerminalMenu.is_active.is_(True),
            ))
            route = db.scalar(select(PosMenuItemRoute).where(
                PosMenuItemRoute.terminal_id == terminal.id,
                PosMenuItemRoute.menu_item_id == line.menu_item_id,
                PosMenuItemRoute.is_active.is_(True),
            ))
            if menu_item is None or terminal_menu is None or route is None:
                raise HTTPException(422, "This menu item is not enabled and routed on this POS terminal")
            price = _menu_price(db, payload.company_id, menu_item, terminal_menu.price_list_id, line.quantity)
            options = _modifier_options(db, payload.company_id, line.modifier_option_ids)
            modifier_delta = sum((Decimal(o.price_delta or 0) for o in options), Decimal("0"))
            base_discount = Decimal(line.discount_percent)
            effective_discount = Decimal("100") - (Decimal("100") - base_discount) * (Decimal("100") - promotion_percent) / Decimal("100")
            lines.append(DocumentLineCreate(
                item_id=menu_item.product_id,
                variant_id=line.variant_id,
                quantity=line.quantity,
                unit_price=price + modifier_delta,
                discount_percent=effective_discount,
            ))
            routes.append(route.station_id)
        else:
            if not line.item_id:
                raise HTTPException(422, "Each POS line requires menu_item_id or item_id")
            if line.unit_price is None:
                raise HTTPException(422, "unit_price is required for a non-menu POS line")
            options = _modifier_options(db, payload.company_id, line.modifier_option_ids)
            modifier_delta = sum((Decimal(o.price_delta or 0) for o in options), Decimal("0"))
            base_discount = Decimal(line.discount_percent)
            effective_discount = Decimal("100") - (Decimal("100") - base_discount) * (Decimal("100") - promotion_percent) / Decimal("100")
            lines.append(DocumentLineCreate(
                item_id=line.item_id,
                variant_id=line.variant_id,
                quantity=line.quantity,
                unit_price=Decimal(line.unit_price) + modifier_delta,
                discount_percent=effective_discount,
            ))
            routes.append(None)

    if payload.promotion_code and promotion_percent:
        estimated_subtotal = sum((Decimal(x.unit_price) * Decimal(x.quantity) for x in lines), Decimal("0"))
        promotion = db.scalar(select(POSPromotion).where(POSPromotion.company_id == payload.company_id, POSPromotion.code == payload.promotion_code, POSPromotion.is_active.is_(True)))
        if promotion is None or estimated_subtotal < Decimal(promotion.min_subtotal or 0):
            raise HTTPException(409, "Promotion minimum subtotal is not met")

    doc = commerce_service.create_document(db, DocumentCreate(
        company_id=payload.company_id,
        partner_id=payload.partner_id,
        document_type="invoice",
        number=payload.number,
        document_date=payload.payment_date,
        warehouse_id=payload.warehouse_id,
        lines=lines,
    ))
    if payload.promotion_code:
        promotion = db.scalar(select(POSPromotion).where(POSPromotion.company_id == payload.company_id, POSPromotion.code == payload.promotion_code, POSPromotion.is_active.is_(True)))
        if promotion is not None:
            discount_value = Decimal(doc.subtotal or 0) * promotion_percent / Decimal("100")
            if promotion.max_discount is not None:
                discount_value = min(discount_value, Decimal(promotion.max_discount))
            db.add(POSPromotionUse(promotion_id=promotion.id, sales_document_id=doc.id, discount_amount=discount_value))
    # POS checkout is a sell + immediate fulfillment. Stocked menu items are issued
    # directly; recipe-backed menu items consume their ingredients from the outlet warehouse.
    direct_lines = []
    recipe_line_ids = set()
    for built_line in doc.lines:
        if _active_recipe(db, payload.company_id, built_line.item_id, built_line.variant_id) is not None:
            recipe_line_ids.add(built_line.id)
        else:
            direct_lines.append(DocumentLineCreate(
                item_id=built_line.item_id, variant_id=built_line.variant_id,
                quantity=built_line.quantity, unit_price=built_line.unit_price,
                discount_percent=built_line.discount_percent,
            ))
    if direct_lines:
        delivery = commerce_service.create_document(db, DocumentCreate(
            company_id=payload.company_id, partner_id=payload.partner_id,
            document_type="delivery", number=f"POSD-{doc.id}",
            document_date=payload.payment_date, warehouse_id=payload.warehouse_id,
            lines=direct_lines,
        ))
        commerce_service.confirm(db, payload.company_id, delivery.id, "sale", current_user.id)
        commerce_service.post_inventory(db, payload.company_id, delivery.id, "sale", user_id=current_user.id)
    outlet_location = db.scalar(select(InventoryLocation).where(
        InventoryLocation.company_id == payload.company_id,
        InventoryLocation.warehouse_id == payload.warehouse_id,
        InventoryLocation.is_active.is_(True),
        InventoryLocation.is_virtual.is_(False),
        InventoryLocation.location_type.in_(["storage", "shipping"]),
    ).order_by(InventoryLocation.id).limit(1))
    if recipe_line_ids:
        if outlet_location is None:
            raise HTTPException(422, "The POS consumption warehouse has no active physical stock location")
        for sale_line in doc.lines:
            if sale_line.id in recipe_line_ids:
                _post_recipe_consumption(
                    db, company_id=payload.company_id, tenant_id=current_user.tenant_id,
                    user_id=current_user.id, sale_id=doc.id, sale_line=sale_line,
                    source_location_id=outlet_location.id, quantity=Decimal(sale_line.quantity),
                    reference=doc.number,
                )
                sale_line.fulfilled_quantity = sale_line.quantity

    snapshot = capture_document_tax_snapshot(db, doc, kind="sale")
    if snapshot is None:
        raise HTTPException(422, "A jurisdiction tax snapshot is required before posting this POS invoice")
    validate_document_tax_snapshot(doc, snapshot)
    commerce_service.confirm(db, payload.company_id, doc.id, "sale", current_user.id)
    # Inventory is fulfilled exactly once by the paired delivery document above.
    commerce_service.pay(db, PaymentCreate(
        company_id=payload.company_id,
        document_id=doc.id,
        payment_date=payload.payment_date,
        amount=doc.total,
        method=payload.method,
    ), "sale", current_user.id)

    for sales_line, station_id in zip(doc.lines, routes):
        if station_id is not None:
            db.add(PosOrderLineRoute(
                sales_line_id=sales_line.id,
                terminal_id=terminal.id,
                station_id=station_id,
                status="queued",
            ))
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/sales/{sale_id}/refund", dependencies=[Depends(require_permission("commerce.payment"))])
def refund_sale(sale_id:int,payload:SalesReturnCreate,current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,payload.company_id,current_user)
    sale=db.scalar(select(SalesDocument).where(SalesDocument.id==sale_id,SalesDocument.company_id==payload.company_id,SalesDocument.document_type=="invoice").with_for_update())
    if sale is None: raise HTTPException(404,"POS sale invoice not found")
    if sale.partner_id != payload.partner_id: raise HTTPException(422,"Refund customer does not match the original sale")
    try:
        result=sales_return_service.create_and_post(db,payload,current_user.id,current_user.tenant_id)
        db.commit();db.refresh(result);return result
    except ValueError as exc:
        db.rollback();raise HTTPException(422,str(exc))

@router.post("/sales/{sale_id}/void", dependencies=[Depends(require_permission("commerce.payment"))])
def void_sale(sale_id:int,company_id:int=Query(...,gt=0),void_date:date=Query(...),current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    _company(db,company_id,current_user)
    sale=db.scalar(select(SalesDocument).where(SalesDocument.id==sale_id,SalesDocument.company_id==company_id,SalesDocument.document_type=="invoice").with_for_update())
    if sale is None: raise HTTPException(404,"POS sale invoice not found")
    if sale.status not in {"confirmed","posted"}: raise HTTPException(409,"Only confirmed/posted POS sales can be voided")
    delivery=db.scalar(select(SalesDocument).where(SalesDocument.company_id==company_id,SalesDocument.number==f"POSD-{sale.id}",SalesDocument.document_type=="delivery").with_for_update())
    if delivery is None: raise HTTPException(409,"POS delivery document was not found")
    from app.modules.commerce.sales_return_schemas import SalesReturnLineCreate
    payload=SalesReturnCreate(company_id=company_id,partner_id=sale.partner_id,number=f"POSVOID-{sale.id}-{void_date.isoformat()}",document_date=void_date,warehouse_id=delivery.warehouse_id,notes=f"POS void for sale {sale.number}",lines=[SalesReturnLineCreate(original_delivery_line_id=line.id,quantity=line.quantity) for line in delivery.lines])
    try:
        result=sales_return_service.create_and_post(db,payload,current_user.id,current_user.tenant_id)
        payments=list(db.scalars(select(CommercePayment).where(CommercePayment.company_id==company_id,CommercePayment.document_kind=="sale",CommercePayment.document_id==sale.id,CommercePayment.status=="posted").with_for_update()).all())
        reversals=[]
        for payment in payments:
            _,_,reversal=reverse_payment(db,company_id=company_id,payment_id=payment.id,reversal_date=void_date,notes=f"POS void {sale.number}")
            reversals.append(reversal.id)
        sale.status="cancelled"
        db.commit()
        return {"sale_id":sale.id,"status":"voided","refund_document_id":result.id,"reversal_payment_ids":reversals}
    except ValueError as exc:
        db.rollback();raise HTTPException(422,str(exc))

@router.get("/stations/{station_id}/queue")
def station_queue(
    station_id: int,
    company_id: int = Query(..., gt=0),
    status: str = Query(default="queued", pattern="^(queued|preparing|ready|served|cancelled)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _company(db, company_id, current_user)
    rows = db.execute(
        select(PosOrderLineRoute, SalesLine, SalesDocument)
        .join(SalesLine, SalesLine.id == PosOrderLineRoute.sales_line_id)
        .join(SalesDocument, SalesDocument.id == SalesLine.document_id)
        .join(PreparationStation, PreparationStation.id == PosOrderLineRoute.station_id)
        .join(Branch, Branch.id == PreparationStation.branch_id)
        .where(
            PosOrderLineRoute.station_id == station_id,
            PosOrderLineRoute.status == status,
            Branch.company_id == company_id,
        )
        .order_by(SalesDocument.document_date.desc(), SalesDocument.id.desc(), SalesLine.id.asc())
        .limit(500)
    ).all()
    return [{
        "route_id": route.id,
        "order_id": doc.id,
        "order_number": doc.number,
        "line_id": line.id,
        "item_id": line.item_id,
        "quantity": line.quantity,
        "description": line.description,
        "status": route.status,
        "terminal_id": route.terminal_id,
        "station_id": route.station_id,
        "notes": route.notes,
    } for route, line, doc in rows]


@router.patch("/order-routes/{route_id}", dependencies=[Depends(require_permission("commerce.post"))])
def update_route(route_id: int, payload: RouteStatusUpdate, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    route = db.scalar(select(PosOrderLineRoute).join(SalesLine, SalesLine.id == PosOrderLineRoute.sales_line_id).join(SalesDocument, SalesDocument.id == SalesLine.document_id).where(
        PosOrderLineRoute.id == route_id,
        SalesDocument.company_id == company_id,
    ).with_for_update())
    if route is None:
        raise HTTPException(404, "POS production route not found")
    allowed = {
        "queued": {"preparing", "cancelled"},
        "preparing": {"ready", "cancelled"},
        "ready": {"served"},
        "served": set(),
        "cancelled": set(),
    }
    if payload.status != route.status and payload.status not in allowed.get(route.status, set()):
        raise HTTPException(409, f"Invalid route transition: {route.status} -> {payload.status}")
    route.status = payload.status
    route.notes = payload.notes
    db.commit()
    db.refresh(route)
    return route


@router.get("/tables")
def list_tables(company_id: int = Query(..., gt=0), branch_id: int | None = Query(default=None, gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    q = select(RestaurantTable).join(Branch, Branch.id == RestaurantTable.branch_id).where(Branch.company_id == company_id, RestaurantTable.is_active.is_(True))
    if branch_id: q = q.where(RestaurantTable.branch_id == branch_id)
    return list(db.scalars(q.order_by(RestaurantTable.branch_id, RestaurantTable.code)).all())

@router.patch("/tables/{table_id}/status", dependencies=[Depends(require_permission("commerce.write"))])
def update_table_status(table_id: int, payload: TableStatusUpdate, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    table = db.scalar(select(RestaurantTable).join(Branch, Branch.id == RestaurantTable.branch_id).where(RestaurantTable.id == table_id, Branch.company_id == company_id, RestaurantTable.is_active.is_(True)).with_for_update())
    if table is None: raise HTTPException(404, "Restaurant table not found")
    if table.status == "out_of_service" and payload.status != "available": raise HTTPException(409, "Out-of-service table must be restored to available first")
    table.status = payload.status
    db.commit(); db.refresh(table); return table

@router.get("/order-types")
def list_order_types(company_id: int = Query(..., gt=0), branch_id: int | None = Query(default=None, gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    q = select(OrderType).join(Branch, Branch.id == OrderType.branch_id).where(Branch.company_id == company_id, OrderType.is_active.is_(True))
    if branch_id: q = q.where(OrderType.branch_id == branch_id)
    return list(db.scalars(q.order_by(OrderType.display_order, OrderType.name)).all())

@router.post("/sales/{sale_id}/split-payments", dependencies=[Depends(require_permission("commerce.payment"))])
def split_payments(sale_id: int, payload: SplitPaymentRequest, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    sale = db.scalar(select(SalesDocument).where(SalesDocument.id == sale_id, SalesDocument.company_id == company_id, SalesDocument.document_type == "invoice").with_for_update())
    if sale is None: raise HTTPException(404, "POS sale invoice not found")
    outstanding = Decimal(sale.total or 0) - Decimal(sale.paid_total or 0)
    total = sum((Decimal(p.amount) for p in payload.payments), Decimal("0"))
    if total != outstanding: raise HTTPException(422, f"Split payments must equal the outstanding amount {outstanding}")
    posted=[]
    for p in payload.payments:
        _, payment = post_payment(db, company_id=company_id, document_kind="sale", document_id=sale.id, amount=p.amount, payment_date=sale.document_date, method=p.method, reference=p.reference, idempotency_key=p.idempotency_key)
        posted.append(payment)
    db.commit(); return {"sale_id": sale.id, "paid_total": sale.paid_total, "payments": posted}

@router.post("/payments/{payment_id}/reverse", dependencies=[Depends(require_permission("commerce.payment"))])
def reverse_pos_payment(payment_id: int, company_id: int = Query(..., gt=0), reversal_date: date = Query(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    _, original, reversal = reverse_payment(db, company_id=company_id, payment_id=payment_id, reversal_date=reversal_date, notes=f"POS payment reversal by user {current_user.id}")
    db.commit(); return {"original_payment_id": original.id, "reversal_payment_id": reversal.id, "status": original.status}

@router.post("/stock-requests", dependencies=[Depends(require_permission("inventory.write"))])
def create_stock_request(payload: TransferCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, payload.company_id, current_user)
    try:
        obj = inventory_transfer_service.create(db, payload)
        inventory_transfer_service.request(db, company_id=payload.company_id, transfer_id=obj.id)
        db.commit(); db.refresh(obj); return obj
    except ValueError as exc:
        db.rollback(); raise HTTPException(422, str(exc))

@router.post("/stock-requests/{transfer_id}/approve", dependencies=[Depends(require_permission("inventory.post"))])
def approve_stock_request(transfer_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    try:
        obj=inventory_transfer_service.approve(db, company_id=company_id, transfer_id=transfer_id); db.commit(); return obj
    except ValueError as exc:
        db.rollback(); raise HTTPException(422,str(exc))

@router.post("/stock-requests/{transfer_id}/ship", dependencies=[Depends(require_permission("inventory.post"))])
def ship_stock_request(transfer_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    try:
        obj=inventory_transfer_service.ship(db, company_id=company_id, transfer_id=transfer_id, tenant_id=current_user.tenant_id, user_id=current_user.id); db.commit(); return obj
    except ValueError as exc:
        db.rollback(); raise HTTPException(422,str(exc))

@router.post("/stock-requests/{transfer_id}/receive", dependencies=[Depends(require_permission("inventory.post"))])
def receive_stock_request(transfer_id: int, company_id: int = Query(..., gt=0), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _company(db, company_id, current_user)
    try:
        obj=inventory_transfer_service.receive(db, company_id=company_id, transfer_id=transfer_id, tenant_id=current_user.tenant_id, user_id=current_user.id); db.commit(); return obj
    except ValueError as exc:
        db.rollback(); raise HTTPException(422,str(exc))
