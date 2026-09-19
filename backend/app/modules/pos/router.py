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
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models.user import User
from app.modules.inventory.items.models import InventoryItem
from app.modules.jurisdiction.commerce_guard import capture_document_tax_snapshot, validate_document_tax_snapshot
from app.modules.restaurant.models import (
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


class Checkout(BaseModel):
    company_id: int = Field(gt=0)
    partner_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    number: str = Field(min_length=1, max_length=60)
    payment_date: date
    method: str = Field(min_length=1, max_length=30)
    terminal_id: int | None = Field(default=None, gt=0)
    lines: list[CheckoutLine] = Field(min_length=1)


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
    if db.scalar(select(PosOutlet).where(PosOutlet.company_id == payload.company_id, PosOutlet.code == payload.code)):
        raise HTTPException(409, "Outlet code already exists")
    obj = PosOutlet(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


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
    lines: list[DocumentLineCreate] = []
    routes: list[int | None] = []
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
            lines.append(DocumentLineCreate(
                item_id=menu_item.product_id,
                variant_id=line.variant_id,
                quantity=line.quantity,
                unit_price=price,
                discount_percent=line.discount_percent,
            ))
            routes.append(route.station_id)
        else:
            if not line.item_id:
                raise HTTPException(422, "Each POS line requires menu_item_id or item_id")
            if line.unit_price is None:
                raise HTTPException(422, "unit_price is required for a non-menu POS line")
            lines.append(DocumentLineCreate(
                item_id=line.item_id,
                variant_id=line.variant_id,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
            ))
            routes.append(None)

    doc = commerce_service.create_document(db, DocumentCreate(
        company_id=payload.company_id,
        partner_id=payload.partner_id,
        document_type="invoice",
        number=payload.number,
        document_date=payload.payment_date,
        warehouse_id=payload.warehouse_id,
        lines=lines,
    ))
    snapshot = capture_document_tax_snapshot(db, doc, kind="sale")
    if snapshot is None:
        raise HTTPException(422, "A jurisdiction tax snapshot is required before posting this POS invoice")
    validate_document_tax_snapshot(doc, snapshot)
    commerce_service.confirm(db, payload.company_id, doc.id, "sale", current_user.id)
    commerce_service.post_inventory(db, payload.company_id, doc.id, "sale", user_id=current_user.id)
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
