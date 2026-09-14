from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import get_effective_tenant_id
from app.core.permissions import require_permission
from app.database.session import get_db
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryResponse,
    CostHistoryCreate,
    MenuCreate,
    MenuItemCreate,
    MenuItemResponse,
    MenuResponse,
    PriceCreate,
    PriceListCreate,
    PriceListResponse,
    PriceResponse,
    PricingAnalysis,
    PricingImpactResponse,
    RecipeCreate,
    RecipeResponse,
)
from app.modules.catalog.service import catalog_service
from app.modules.companies.models import Company
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.saas.entitlements import require_module

router = APIRouter(prefix="/catalog", tags=["Product Catalog"])
GUARDS = [Depends(require_permission("inventory.access")), Depends(require_module("inventory"))]
WRITE_GUARDS = [Depends(require_permission("inventory.write")), Depends(require_module("inventory"))]


def _company_for_user(db: Session, company_id: int, user: User) -> Company:
    tenant_id = get_effective_tenant_id(user)
    company = db.scalar(select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id))
    if company is None:
        raise HTTPException(status_code=403, detail="Company is outside the current tenant")
    if not company.is_active:
        raise HTTPException(status_code=409, detail="Company is inactive")
    return company


def _error(exc: ValueError):
    text = str(exc)
    lowered = text.lower()
    if "not found" in lowered:
        status = 404
    elif "outside the current tenant" in lowered:
        status = 403
    else:
        status = 409
    raise HTTPException(status_code=status, detail=text) from exc


def _recipe_response(db, company_id, recipe):
    cost = catalog_service.recipe_cost(db, company_id, recipe.id)
    return {
        **recipe.__dict__,
        "lines": [
            {
                "id": l.id,
                "line_no": l.line_no,
                "ingredient_product_id": l.ingredient_product_id,
                "quantity": l.quantity,
                "waste_percentage": l.waste_percentage,
                "uom_id": l.uom_id,
                "notes": l.notes,
            }
            for l in recipe.lines
        ],
        "total_cost": cost * recipe.yield_quantity,
        "cost_per_yield": cost,
    }


@router.post("/categories", response_model=CategoryResponse, status_code=201, dependencies=WRITE_GUARDS)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, current_user)
    try:
        return catalog_service.create_category(db, payload)
    except ValueError as exc:
        _error(exc)


@router.get("/categories", response_model=list[CategoryResponse], dependencies=GUARDS)
def list_categories(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.list_categories(db, company_id)
    except ValueError as exc:
        _error(exc)


@router.post("/price-lists", response_model=PriceListResponse, status_code=201, dependencies=WRITE_GUARDS)
def create_price_list(payload: PriceListCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, current_user)
    try:
        return catalog_service.create_price_list(db, payload)
    except ValueError as exc:
        _error(exc)


@router.get("/price-lists", response_model=list[PriceListResponse], dependencies=GUARDS)
def list_price_lists(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.list_price_lists(db, company_id)
    except ValueError as exc:
        _error(exc)


@router.post("/prices", response_model=PriceResponse, status_code=201, dependencies=WRITE_GUARDS)
def create_price(payload: PriceCreate, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.create_price(db, company_id, payload)
    except ValueError as exc:
        _error(exc)


@router.get("/prices", response_model=list[PriceResponse], dependencies=GUARDS)
def list_prices(company_id: int = Query(..., gt=0), product_id: int | None = Query(default=None, gt=0), price_list_id: int | None = Query(default=None, gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.list_prices(db, company_id, product_id, price_list_id)
    except ValueError as exc:
        _error(exc)


@router.post("/products/{product_id}/base-price", dependencies=WRITE_GUARDS)
def set_base_price(product_id: int, sale_price: Decimal = Query(..., ge=0), company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        product = catalog_service.set_base_price(db, company_id, product_id, sale_price)
        return {"success": True, "data": {"product_id": product.id, "sales_price": product.sales_price}}
    except ValueError as exc:
        _error(exc)


@router.post("/cost-history", status_code=201, dependencies=WRITE_GUARDS)
def record_cost(payload: CostHistoryCreate, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        row = catalog_service.record_cost(db, company_id, payload)
        return {"success": True, "data": {"id": row.id, "product_id": row.product_id, "cost": row.cost, "effective_at": row.effective_at}}
    except ValueError as exc:
        _error(exc)


@router.get("/products/{product_id}/cost-history", dependencies=GUARDS)
def list_cost_history(product_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.list_cost_history(db, company_id, product_id)
    except ValueError as exc:
        _error(exc)


@router.post("/recipes", response_model=RecipeResponse, status_code=201, dependencies=WRITE_GUARDS)
def create_recipe(payload: RecipeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, current_user)
    try:
        return _recipe_response(db, payload.company_id, catalog_service.create_recipe(db, payload))
    except ValueError as exc:
        _error(exc)


@router.get("/recipes", response_model=list[RecipeResponse], dependencies=GUARDS)
def list_recipes(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return [_recipe_response(db, company_id, r) for r in catalog_service.list_recipes(db, company_id)]
    except ValueError as exc:
        _error(exc)


@router.get("/recipes/{recipe_id}", response_model=RecipeResponse, dependencies=GUARDS)
def get_recipe(recipe_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return _recipe_response(db, company_id, catalog_service.get_recipe(db, company_id, recipe_id))
    except ValueError as exc:
        _error(exc)


@router.post("/menus", response_model=MenuResponse, status_code=201, dependencies=WRITE_GUARDS)
def create_menu(payload: MenuCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, payload.company_id, current_user)
    try:
        return catalog_service.create_menu(db, payload)
    except ValueError as exc:
        _error(exc)


@router.get("/menus", response_model=list[MenuResponse], dependencies=GUARDS)
def list_menus(company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.list_menus(db, company_id)
    except ValueError as exc:
        _error(exc)


@router.get("/menus/{menu_id}", response_model=MenuResponse, dependencies=GUARDS)
def get_menu(menu_id: int, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.get_menu(db, company_id, menu_id)
    except ValueError as exc:
        _error(exc)


@router.post("/menus/{menu_id}/items", response_model=MenuItemResponse, status_code=201, dependencies=WRITE_GUARDS)
def add_menu_item(menu_id: int, payload: MenuItemCreate, company_id: int = Query(..., gt=0), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.add_menu_item(db, company_id, menu_id, payload)
    except ValueError as exc:
        _error(exc)


@router.get("/products/{product_id}/pricing-analysis", response_model=PricingAnalysis, dependencies=GUARDS)
def pricing_analysis(product_id: int, company_id: int = Query(..., gt=0), price_list_id: int | None = Query(default=None, gt=0), target_margin: Decimal = Query(default=Decimal("30"), ge=0, lt=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.pricing_analysis(db, company_id, product_id, target_margin, price_list_id)
    except ValueError as exc:
        _error(exc)


@router.get("/pricing-impact", response_model=PricingImpactResponse, dependencies=GUARDS)
def pricing_impact(company_id: int = Query(..., gt=0), price_list_id: int | None = Query(default=None, gt=0), target_margin: Decimal = Query(default=Decimal("30"), ge=0, lt=100), below_margin: Decimal | None = Query(default=None, ge=0, lt=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _company_for_user(db, company_id, current_user)
    try:
        return catalog_service.pricing_impact(db, company_id, target_margin, price_list_id, below_margin)
    except ValueError as exc:
        _error(exc)
