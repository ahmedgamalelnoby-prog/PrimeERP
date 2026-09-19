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
from app.modules.accounting.reports.service import financial_report_service
from app.modules.platform.module_registry import REGISTRY_VERSION, knowledge_context

router = APIRouter(prefix="/helpdesk", tags=["helpdesk"])



class HelpdeskQuestion(BaseModel):
    company_id: int = Field(gt=0)
    question: str = Field(min_length=2, max_length=4000)
    language: str = Field(default="ar", pattern="^(ar|en)$")
    conversation: list[dict[str, str]] = Field(default_factory=list, max_length=20)

class HelpdeskAnswer(BaseModel):
    answer: str
    source: str
    suggested_actions: list[str] = Field(default_factory=list)


class AdvisoryRequest(BaseModel):
    company_id: int = Field(gt=0)
    focus: str = Field(default="general", min_length=1, max_length=80)
    question: str | None = Field(default=None, max_length=2000)
    from_date: str | None = None
    to_date: str | None = None
    language: str = Field(default="ar", pattern="^(ar|en)$")


class AdvisoryResponse(BaseModel):
    summary: str
    priorities: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    knowledge_version: str
    ai_provider: str

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
MODULE REGISTRY VERSION: {REGISTRY_VERSION}
LIVE MODULE KNOWLEDGE:
{knowledge_context()}
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
            json={"model": settings.AI_MODEL, "messages": messages, "temperature": 0.2, "max_tokens": settings.AI_MAX_OUTPUT_TOKENS, "response_format": {"type": "json_object"}},
            timeout=45,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload: dict[str, Any] = json.loads(content)
        answer = str(payload.get("answer") or "").strip()
        if not answer:
            return fallback
        actions = [str(x) for x in payload.get("suggested_actions", []) if str(x).strip()][:5]
        return HelpdeskAnswer(answer=answer, source=f"openai:{REGISTRY_VERSION}", suggested_actions=actions)
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


@router.post("/ai/advice", response_model=AdvisoryResponse)
def business_advice(
    request: AdvisoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdvisoryResponse:
    if not settings.AI_ADVISORY_ENABLED:
        raise HTTPException(status_code=404, detail="AI advisory is disabled")
    from datetime import date

    from_date = None
    to_date = None
    try:
        if request.from_date:
            from_date = date.fromisoformat(request.from_date)
        if request.to_date:
            to_date = date.fromisoformat(request.to_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Dates must use YYYY-MM-DD") from exc
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date cannot be after to_date")

    from app.models.company import Company
    company = db.get(Company, request.company_id)
    if company is None or getattr(company, "tenant_id", None) != get_effective_tenant_id(current_user):
        raise HTTPException(status_code=404, detail="Company not found")

    summary = financial_report_service.financial_summary(
        db,
        tenant_id=get_effective_tenant_id(current_user),
        company_id=request.company_id,
        from_date=from_date,
        to_date=to_date,
    )
    metrics = {
        "revenue": float(summary.revenue),
        "expenses": float(summary.expenses),
        "net_profit": float(summary.net_profit),
        "assets": float(summary.assets),
        "liabilities": float(summary.liabilities),
        "equity": float(summary.equity),
    }
    margin = round(metrics["net_profit"] / metrics["revenue"] * 100, 2) if metrics["revenue"] else None
    if margin is not None:
        metrics["net_margin_pct"] = margin

    priorities: list[str] = []
    if margin is not None and margin < 10:
        priorities.append("Review profitability and cost drivers.")
    if metrics["liabilities"] > metrics["assets"] and metrics["assets"] > 0:
        priorities.append("Review leverage, liquidity and near-term obligations.")
    if not priorities:
        priorities.append("Maintain current controls and review trend changes before taking action.")

    fallback = AdvisoryResponse(
        summary="PrimeERP reviewed the current financial snapshot and identified practical improvement priorities.",
        priorities=priorities,
        recommendations=[
            "Compare revenue, expenses and net margin by month or operating segment.",
            "Review overdue receivables, payment commitments and cash requirements.",
            "Use the relevant operational module and schedule a recurring management report for trend monitoring.",
        ],
        next_steps=[
            "Validate the recommendation against the underlying transaction data.",
            "Assign an owner and due date to each action.",
            "Re-run the advisory review after the next reporting period.",
        ],
        knowledge_version=REGISTRY_VERSION,
        ai_provider="prime_rules",
    )
    if not settings.OPENAI_API_KEY:
        return fallback

    system = f"""You are PrimeERP Business Advisor.
Use only the supplied live financial snapshot and PrimeERP module knowledge.
Never invent values, transactions, features, regulations or implementation status.
Give practical, measurable advice for management. Separate observations from recommendations.
Return strict JSON with keys: summary, priorities, recommendations, next_steps.
Answer in {'Arabic' if request.language == 'ar' else 'English'}.
Module knowledge version: {REGISTRY_VERSION}
MODULE KNOWLEDGE:
{knowledge_context()}
LIVE METRICS:
{json.dumps(metrics, ensure_ascii=False)}
FOCUS: {request.focus}
QUESTION: {request.question or 'Provide the most useful improvement plan for the current snapshot.'}
"""
    try:
        response = requests.post(
            f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": settings.AI_MODEL,
                "messages": [{"role": "system", "content": system}],
                "temperature": 0.15,
                "max_tokens": settings.AI_MAX_OUTPUT_TOKENS,
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = json.loads(response.json()["choices"][0]["message"]["content"])
        return AdvisoryResponse(
            summary=str(payload.get("summary") or fallback.summary),
            priorities=[str(x) for x in payload.get("priorities", []) if str(x).strip()][:6],
            recommendations=[str(x) for x in payload.get("recommendations", []) if str(x).strip()][:8],
            next_steps=[str(x) for x in payload.get("next_steps", []) if str(x).strip()][:8],
            knowledge_version=REGISTRY_VERSION,
            ai_provider="openai_compatible",
        )
    except (requests.RequestException, KeyError, IndexError, TypeError, json.JSONDecodeError):
        return fallback.model_copy(update={"ai_provider": "prime_rules_after_provider_error"})
