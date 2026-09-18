from __future__ import annotations

import json
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.database.session import get_db
from sqlalchemy.orm import Session
from app.core.context import get_effective_tenant_id

router = APIRouter(prefix="/helpdesk", tags=["helpdesk"])


PRODUCT_CONTEXT = """
PrimeERP is a multi-tenant SaaS ERP platform. Core areas include:
Finance: Accounting, Treasury, Invoicing, Taxes, Assets, Budgets, Cost Centers, Egyptian e-Invoice.
Commercial: CRM, Sales, Purchasing, POS, Subscriptions, Rentals, Loyalty, Promotions, Commissions.
Operations: Inventory, Catalog, UOM, Shipping, Manufacturing, Quality, Maintenance, Restaurant, Work Orders.
Enterprise: Companies, Branches, Users, Roles, Permissions, Audit, HR, Projects, Contracts, Documents, Reports.
Platform: Tenants, Plans, Subscriptions, Entitlements, Integrations, Notifications.
PrimeERP also provides AI business analytics and scheduled report delivery by email/WhatsApp when configured.
"""

class HelpdeskQuestion(BaseModel):
    company_id: int = Field(gt=0)
    question: str = Field(min_length=2, max_length=4000)
    language: str = Field(default="ar", pattern="^(ar|en)$")
    conversation: list[dict[str, str]] = Field(default_factory=list, max_length=20)

class HelpdeskAnswer(BaseModel):
    answer: str
    source: str
    suggested_actions: list[str] = Field(default_factory=list)

def _fallback(question: str, language: str) -> HelpdeskAnswer:
    q = question.lower()
    if any(word in q for word in ("invoice", "فاتورة", "فواتير")):
        ar = "يمكنك إدارة فواتير المبيعات والمشتريات وربطها بالمحاسبة والضرائب والتحصيل. إذا أخبرتني نوع الفاتورة والعملية التي تريد تنفيذها سأشرح لك الخطوات."
        en = "PrimeERP manages sales and purchase invoices and connects them to accounting, taxes and collections. Tell me the invoice type and I can guide you step by step."
    elif any(word in q for word in ("inventory", "stock", "مخزون", "مخزن")):
        ar = "موديول المخزون يدير الأصناف والمخازن والمواقع وحركات الاستلام والتسليم والتحويل والجرد والتكلفة."
        en = "The Inventory module manages products, warehouses, locations, receipts, deliveries, transfers, stock counts and valuation."
    elif any(word in q for word in ("subscription", "اشتراك", "باقة")):
        ar = "PrimeERP SaaS يدعم الباقات والاشتراكات والتجارب والصلاحيات حسب الـEntitlements. يمكن إدارة مدة التجربة وحالة الاشتراك والوصول للموديولات."
        en = "PrimeERP SaaS supports plans, subscriptions, trials and module entitlements, including trial duration, subscription status and module access."
    elif any(word in q for word in ("help", "مساعدة", "مشكلة", "support", "دعم")):
        ar = "أنا مساعد PrimeERP. أستطيع شرح الموديولات والعمليات، مساعدتك في الوصول للوظيفة الصحيحة، وتوضيح خطوات العمل. لا ترسل كلمات المرور أو مفاتيح API."
        en = "I am the PrimeERP AI assistant. I can explain modules and workflows, help you find the right function and guide you through operations. Do not share passwords or API keys."
    else:
        ar = "أستطيع مساعدتك في فهم PrimeERP وموديولاته وشرح خطوات العمل. اكتب سؤالك بالتفصيل، وسأحاول توجيهك للوظيفة أو الموديول المناسب."
        en = "I can help you understand PrimeERP, its modules and workflows. Describe your question and I will guide you to the relevant function or module."
    return HelpdeskAnswer(answer=ar if language == "ar" else en, source="primeerp_fallback", suggested_actions=[])

def _ask_ai(request: HelpdeskQuestion) -> HelpdeskAnswer:
    fallback = _fallback(request.question, request.language)
    if not settings.OPENAI_API_KEY:
        return fallback
    system = f"""You are PrimeERP Help Desk AI.
Answer customer questions about PrimeERP accurately and concisely.
Use only the product context below. Never invent a feature, endpoint, policy, price, legal requirement, or completed implementation.
If the question is outside PrimeERP, say that it is outside the available product context.
If the customer asks for a procedure, provide numbered steps.
Protect secrets: never request or expose passwords, access tokens, API keys, or private tenant data.
Respond in {'Arabic' if request.language == 'ar' else 'English'}.
Return strict JSON with keys: answer, suggested_actions.
PRODUCT CONTEXT:
{PRODUCT_CONTEXT}
"""
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for item in request.conversation[-10:]:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content[:4000]})
    messages.append({"role": "user", "content": request.question})
    try:
        response = requests.post(
            f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": settings.AI_MODEL, "messages": messages, "temperature": 0.2, "response_format": {"type": "json_object"}},
            timeout=45,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload: dict[str, Any] = json.loads(content)
        answer = str(payload.get("answer") or "").strip()
        if not answer:
            return fallback
        actions = [str(x) for x in payload.get("suggested_actions", []) if str(x).strip()][:5]
        return HelpdeskAnswer(answer=answer, source="openai", suggested_actions=actions)
    except (requests.RequestException, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="AI help desk is temporarily unavailable") from exc

@router.post("/ai/answer", response_model=HelpdeskAnswer)
def answer_helpdesk(
    request: HelpdeskQuestion,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HelpdeskAnswer:
    from app.models.company import Company
    company = db.get(Company, request.company_id)
    if company is None or getattr(company, "tenant_id", None) != get_effective_tenant_id(current_user):
        raise HTTPException(status_code=404, detail="Company not found")
    return _ask_ai(request)
