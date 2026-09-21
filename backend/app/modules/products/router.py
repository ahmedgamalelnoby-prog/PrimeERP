from fastapi import APIRouter,Depends,HTTPException,Query,status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from .models import Product,ProductCategory,ProductUnit
from .schemas import *
router=APIRouter(prefix="/products",tags=["products"])
def _tenant(u:User)->int:
    if u.is_platform_admin or u.tenant_id is None: raise HTTPException(403,"Active tenant context is required")
    return u.tenant_id
def _get(db,model,tenant_id,id):
    obj=db.scalar(select(model).where(model.id==id,model.tenant_id==tenant_id))
    if obj is None: raise HTTPException(404,f"{model.__name__} not found")
    return obj
@router.get("/categories",response_model=list[CategoryRead])
def categories(db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    return list(db.scalars(select(ProductCategory).where(ProductCategory.tenant_id==_tenant(u)).order_by(ProductCategory.name)).all())
@router.post("/categories",response_model=CategoryRead,status_code=201)
def create_category(p:CategoryCreate,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    obj=ProductCategory(tenant_id=_tenant(u),**p.model_dump());db.add(obj)
    try: db.commit()
    except IntegrityError as e: db.rollback();raise HTTPException(409,"Category code already exists") from e
    db.refresh(obj);return obj
@router.get("/units",response_model=list[UnitRead])
def units(db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    return list(db.scalars(select(ProductUnit).where(ProductUnit.tenant_id==_tenant(u)).order_by(ProductUnit.name)).all())
@router.post("/units",response_model=UnitRead,status_code=201)
def create_unit(p:UnitCreate,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    obj=ProductUnit(tenant_id=_tenant(u),**p.model_dump());db.add(obj)
    try: db.commit()
    except IntegrityError as e: db.rollback();raise HTTPException(409,"Unit code already exists") from e
    db.refresh(obj);return obj
@router.get("",response_model=list[ProductRead])
def products(search:str|None=Query(None),active_only:bool=False,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    stmt=select(Product).where(Product.tenant_id==_tenant(u))
    if active_only: stmt=stmt.where(Product.is_active.is_(True))
    if search: stmt=stmt.where(Product.name.ilike(f"%{search}%"))
    return list(db.scalars(stmt.order_by(Product.name,Product.id)).all())
@router.get("/{product_id}",response_model=ProductRead)
def get_product(product_id:int,db:Session=Depends(get_db),u:User=Depends(get_current_user)): return _get(db,Product,_tenant(u),product_id)
@router.post("",response_model=ProductRead,status_code=201)
def create_product(p:ProductCreate,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    tid=_tenant(u); _get(db,ProductUnit,tid,p.unit_id)
    if p.category_id is not None: _get(db,ProductCategory,tid,p.category_id)
    obj=Product(tenant_id=tid,**p.model_dump());db.add(obj)
    try: db.commit()
    except IntegrityError as e: db.rollback();raise HTTPException(409,"Product SKU already exists") from e
    db.refresh(obj);return obj
@router.put("/{product_id}",response_model=ProductRead)
def update_product(product_id:int,p:ProductUpdate,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    tid=_tenant(u);obj=_get(db,Product,tid,product_id);data=p.model_dump(exclude_unset=True)
    if "unit_id" in data: _get(db,ProductUnit,tid,data["unit_id"])
    if data.get("category_id") is not None: _get(db,ProductCategory,tid,data["category_id"])
    for k,v in data.items():setattr(obj,k,v)
    try: db.commit()
    except IntegrityError as e: db.rollback();raise HTTPException(409,"Product SKU already exists") from e
    db.refresh(obj);return obj
