from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.modules.accounting.chart_of_accounts.models import AccountingDepartment,AccountingCostCenter,NaturalAccount,AccountCombination
from app.modules.companies.models import Company
from app.modules.branches.models import Branch
class ChartOfAccountsService:
 def tenant(self,u):
  if u.is_platform_admin or u.tenant_id is None: raise HTTPException(403,"An active tenant context is required")
  return u.tenant_id
 def company(self,db,t,cid):
  c=db.query(Company).filter(Company.id==cid,Company.tenant_id==t).first()
  if not c: raise HTTPException(404,"Company not found")
 def departments(self,db,u,cid):
  t=self.tenant(u); self.company(db,t,cid); return db.query(AccountingDepartment).filter(AccountingDepartment.company_id==cid).order_by(AccountingDepartment.code).all()
 def create_department(self,db,p,u):
  t=self.tenant(u); self.company(db,t,p.company_id); o=AccountingDepartment(**p.model_dump()); db.add(o)
  try: db.commit(); db.refresh(o); return o
  except IntegrityError as e: db.rollback(); raise HTTPException(409,"Department code already exists") from e
 def cost_centers(self,db,u,cid):
  t=self.tenant(u); self.company(db,t,cid); return db.query(AccountingCostCenter).filter(AccountingCostCenter.company_id==cid).order_by(AccountingCostCenter.code).all()
 def create_cost_center(self,db,p,u):
  t=self.tenant(u); self.company(db,t,p.company_id)
  d=db.query(AccountingDepartment).filter(AccountingDepartment.id==p.department_id,AccountingDepartment.company_id==p.company_id).first()
  if not d: raise HTTPException(404,"Department not found for company")
  if p.branch_id and not db.query(Branch).filter(Branch.id==p.branch_id,Branch.company_id==p.company_id,Branch.tenant_id==t).first(): raise HTTPException(404,"Branch not found for company")
  o=AccountingCostCenter(**p.model_dump()); db.add(o)
  try: db.commit(); db.refresh(o); return o
  except IntegrityError as e: db.rollback(); raise HTTPException(409,"Cost center code already exists") from e
 def natural_accounts(self,db,u,cid):
  t=self.tenant(u); self.company(db,t,cid); return db.query(NaturalAccount).filter(NaturalAccount.company_id==cid).order_by(NaturalAccount.code).all()
 def create_natural_account(self,db,p,u):
  t=self.tenant(u); self.company(db,t,p.company_id)
  if p.parent_id and not db.query(NaturalAccount).filter(NaturalAccount.id==p.parent_id,NaturalAccount.company_id==p.company_id).first(): raise HTTPException(404,"Parent account not found")
  o=NaturalAccount(**p.model_dump()); db.add(o)
  try: db.commit(); db.refresh(o); return o
  except IntegrityError as e: db.rollback(); raise HTTPException(409,"Natural account code already exists") from e
 def combinations(self,db,u,cid):
  t=self.tenant(u); self.company(db,t,cid); return db.query(AccountCombination).filter(AccountCombination.company_id==cid).order_by(AccountCombination.code).all()
 def create_combination(self,db,p,u):
  t=self.tenant(u); self.company(db,t,p.company_id)
  d=db.query(AccountingDepartment).filter(AccountingDepartment.id==p.department_id,AccountingDepartment.company_id==p.company_id).first()
  cc=db.query(AccountingCostCenter).filter(AccountingCostCenter.id==p.cost_center_id,AccountingCostCenter.company_id==p.company_id,AccountingCostCenter.department_id==p.department_id).first()
  na=db.query(NaturalAccount).filter(NaturalAccount.id==p.natural_account_id,NaturalAccount.company_id==p.company_id).first()
  if not d or not cc or not na: raise HTTPException(404,"Account dimensions must belong to company and match")
  o=AccountCombination(company_id=p.company_id,department_id=p.department_id,cost_center_id=p.cost_center_id,natural_account_id=p.natural_account_id,code=f"{d.code}{cc.code}{na.code}",name_ar=p.name_ar or na.name_ar,name_en=p.name_en or na.name_en,opening_debit=p.opening_debit,opening_credit=p.opening_credit,is_active=p.is_active); db.add(o)
  try: db.commit(); db.refresh(o); return o
  except IntegrityError as e: db.rollback(); raise HTTPException(409,"Account combination already exists") from e
chart_service=ChartOfAccountsService()
