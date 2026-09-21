from typing import Optional
from fastapi import APIRouter,Depends,Query,status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.accounting.journals.schemas.journal import JournalCreate,JournalUpdate,JournalResponse,JournalEntryCreate,JournalEntryUpdate,JournalEntryResponse,JournalEntryAction
from app.modules.accounting.journals.services.journal_service import journal_service
router=APIRouter()
@router.get("/journals",response_model=list[JournalResponse])
def list_journals(company_id:Optional[int]=Query(None,gt=0),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.list_journals(db,current_user,company_id)
@router.post("/journals",response_model=JournalResponse,status_code=status.HTTP_201_CREATED)
def create_journal(payload:JournalCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.create_journal(db,payload,current_user)
@router.get("/journals/{journal_id}",response_model=JournalResponse)
def get_journal(journal_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.get_journal(db,journal_id,current_user)
@router.put("/journals/{journal_id}",response_model=JournalResponse)
def update_journal(journal_id:int,payload:JournalUpdate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.update_journal(db,journal_id,payload,current_user)
@router.get("/journal-entries",response_model=list[JournalEntryResponse])
def list_entries(company_id:Optional[int]=Query(None,gt=0),entry_status:Optional[str]=Query(None,alias="status"),db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.list_entries(db,current_user,company_id,entry_status)
@router.post("/journal-entries",response_model=JournalEntryResponse,status_code=status.HTTP_201_CREATED)
def create_entry(payload:JournalEntryCreate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.create_entry(db,payload,current_user)
@router.get("/journal-entries/{entry_id}",response_model=JournalEntryResponse)
def get_entry(entry_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.get_entry(db,entry_id,current_user)
@router.put("/journal-entries/{entry_id}",response_model=JournalEntryResponse)
def update_entry(entry_id:int,payload:JournalEntryUpdate,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.update_entry(db,entry_id,payload,current_user)
@router.post("/journal-entries/{entry_id}/submit",response_model=JournalEntryResponse)
def submit(entry_id:int,payload:JournalEntryAction,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.submit(db,entry_id,current_user)
@router.post("/journal-entries/{entry_id}/approve",response_model=JournalEntryResponse)
def approve(entry_id:int,payload:JournalEntryAction,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.approve(db,entry_id,current_user)
@router.post("/journal-entries/{entry_id}/post",response_model=JournalEntryResponse)
def post(entry_id:int,payload:JournalEntryAction,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.post(db,entry_id,current_user)
@router.post("/journal-entries/{entry_id}/cancel",response_model=JournalEntryResponse)
def cancel(entry_id:int,payload:JournalEntryAction,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)): return journal_service.cancel(db,entry_id,current_user)
