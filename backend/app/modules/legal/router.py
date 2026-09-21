from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.modules.identity.dependencies import get_current_user
from app.modules.identity.models import User
from app.modules.legal.models import LegalAcceptance, LegalDocument

router = APIRouter(prefix="/legal", tags=["legal"])

DEFAULTS = {
    "terms": {
        "title_ar": "شروط استخدام PrimeERP",
        "title_en": "PrimeERP Terms of Use",
        "content_ar": """مرحبًا بك في PrimeERP، منصة لإدارة موارد المؤسسة والعمليات المالية والتشغيلية وفق الخطة والصلاحيات الممنوحة.

1. الاستخدام المصرح به
يُستخدم النظام لأغراض الأعمال المشروعة ولإدارة بيانات المؤسسة وعملياتها. يلتزم كل مستخدم باستخدام حسابه وعدم مشاركة بيانات الدخول أو محاولة تجاوز ضوابط الوصول.

2. الحسابات والصلاحيات
المستخدم مسؤول عن سرية بيانات الدخول وعن النشاط المنفذ من حسابه. يحق لمدير النظام إنشاء الحسابات والأدوار وتعديلها أو إيقافها وفق احتياجات المؤسسة.

3. البيانات والمعاملات
يجب إدخال بيانات صحيحة ومحدثة. تظل المؤسسة والمستخدمون المخولون مسؤولين عن مراجعة واعتماد القيود والفواتير والمدفوعات والمخزون والعقود والتقارير.

4. التقارير والتكاملات
قد تعتمد بعض الوظائف على تكاملات أو خدمات خارجية. يجب مراجعة نتائج التكامل والتقارير قبل الاعتماد عليها، خصوصًا للمتطلبات المحاسبية أو الضريبية أو التنظيمية.

5. الأمان والاستخدام المقبول
يُحظر تعطيل الخدمة أو محاولة الوصول غير المصرح به إلى البيانات أو الوظائف أو حسابات المستخدمين الآخرين. قد يحتفظ النظام بسجلات تشغيل ومراجعة لأغراض الأمن والحوكمة.

6. الاشتراكات والوحدات
تختلف الوحدات والحدود المتاحة بحسب الخطة والاشتراك وإعدادات المنصة. قد يتم تقييد الوصول عند انتهاء التجربة أو الاشتراك.

7. التعديلات والإصدارات
يمكن لمالك المنصة أو مديرها المخول تحديث هذه الشروط. الإصدار المنشور هو المرجع الحالي، وقد يُطلب من المستخدم قبول الإصدار الجديد قبل متابعة الاستخدام.

8. المسؤولية
PrimeERP أداة لإدارة الأعمال ولا يحل محل المراجعة المهنية أو القانونية أو الضريبية. تقع مسؤولية القرارات والبيانات والالتزامات على المؤسسة والمستخدمين المخولين.

9. التواصل
تُوجَّه استفسارات الخدمة إلى مسؤول النظام أو جهة الدعم المعتمدة لدى المؤسسة.""",
        "content_en": """Welcome to PrimeERP, an enterprise resource management platform for financial and operational business processes according to the plan and permissions assigned to each user.

1. Authorized Use
PrimeERP is intended for lawful business use and management of organization data and operations. Users must use their own accounts, protect credentials and must not bypass access controls.

2. Accounts and Permissions
Users are responsible for credential confidentiality and activity performed through their accounts. Authorized administrators may create, modify or deactivate accounts and roles according to organizational needs.

3. Data and Transactions
Information should be accurate and current. The organization and authorized users remain responsible for reviewing and approving accounting entries, invoices, payments, inventory, contracts and reports.

4. Reports and Integrations
Some functionality may depend on external integrations or services. Users should review integration results and reports before relying on them, especially for accounting, tax or regulatory requirements.

5. Security and Acceptable Use
Users must not disrupt the service or attempt unauthorized access to data, functions or other accounts. The system may maintain operational and audit records for security and governance.

6. Subscriptions and Modules
Available modules and limits depend on the selected plan, subscription and platform settings. Access may be restricted after a trial or subscription expires.

7. Updates and Versions
The platform owner or authorized administrator may update these terms. The published version is the current reference and users may be required to accept a new version before continuing to use the service.

8. Responsibility
PrimeERP is a business management tool and does not replace professional accounting, legal or tax review. The organization and authorized users remain responsible for decisions, data and obligations.

9. Contact
Service questions should be directed to the organization's administrator or authorized support channel."""
    },
    "privacy": {
        "title_ar": "سياسة خصوصية PrimeERP",
        "title_en": "PrimeERP Privacy Policy",
        "content_ar": """توضح هذه السياسة كيفية التعامل بصورة عامة مع البيانات داخل PrimeERP، ويمكن لمالك المنصة تعديلها لتناسب نشاط المؤسسة ومتطلبات الخصوصية المطبقة عليها.

1. البيانات التي قد تُعالج
قد يعالج النظام بيانات الحسابات والمستخدمين، بيانات المؤسسة والفروع، السجلات المالية والتشغيلية، سجلات المراجعة والنشاط، وبيانات الاستخدام اللازمة لتشغيل الخدمة.

2. أغراض الاستخدام
تُستخدم البيانات لتشغيل وحدات PrimeERP، تنفيذ العمليات المصرح بها، دعم الأمان والحوكمة، إعداد التقارير، إدارة الاشتراكات وتقديم الدعم.

3. الوصول والصلاحيات
يتم الوصول إلى البيانات وفق الأدوار والصلاحيات وإعدادات المؤسسة. يجب منح الوصول فقط للمستخدمين الذين يحتاجونه لأغراض عمل مشروعة.

4. حماية البيانات
تستخدم المنصة ضوابط وصول وسجلات مراجعة وإجراءات أمنية مناسبة لطبيعة النظام. لا يمكن ضمان أمان مطلق لأي خدمة تقنية، ولذلك يجب إدارة الحسابات والصلاحيات وأجهزة المستخدمين بعناية.

5. الاحتفاظ والحذف
قد يتم الاحتفاظ بالبيانات للمدة اللازمة للتشغيل أو للمتطلبات القانونية أو المحاسبية أو التعاقدية. تخضع عمليات الحذف والاحتفاظ لإعدادات المنصة والتزامات المؤسسة.

6. التكاملات الخارجية
قد تستخدم بعض الوظائف خدمات أو تكاملات خارجية. يخضع تبادل البيانات لنطاق التكامل وإعداداته والسياسات والشروط ذات الصلة.

7. بيانات الموظفين والعملاء والموردين
تتحمل المؤسسة مسؤولية التأكد من أن جمع واستخدام البيانات الشخصية يتوافق مع الأساس القانوني والسياسات الداخلية والمتطلبات التنظيمية المطبقة.

8. تحديث السياسة
يمكن لمالك المنصة نشر إصدار محدث من سياسة الخصوصية، وقد يُطلب من المستخدمين الاطلاع عليه أو قبوله.

9. التواصل
تُوجَّه الاستفسارات المتعلقة بالخصوصية إلى مسؤول النظام أو جهة الخصوصية المعتمدة لدى المؤسسة.""",
        "content_en": """This policy describes, at a general level, how data may be handled within PrimeERP. The platform owner may adapt it to the organization's activities and applicable privacy requirements.

1. Data We May Process
PrimeERP may process account and user data, organization and branch data, financial and operational records, audit and activity logs, and usage data required to operate the service.

2. Purposes
Data may be used to operate PrimeERP modules, execute authorized transactions, support security and governance, produce reports, administer subscriptions and provide support.

3. Access and Permissions
Access is controlled through roles, permissions and organization settings. Access should be granted only to users who need it for legitimate business purposes.

4. Data Protection
The platform uses access controls, audit records and security measures appropriate to the system. No technology service can guarantee absolute security, so organizations should carefully manage accounts, permissions and user devices.

5. Retention and Deletion
Data may be retained as necessary for operation or applicable legal, accounting or contractual requirements. Deletion and retention remain subject to platform settings and the organization's obligations.

6. External Integrations
Some features may use external services or integrations. Data exchanged through them is governed by the scope and configuration of the integration and relevant terms and policies.

7. Employee, Customer and Supplier Data
The organization is responsible for ensuring that collection and use of personal data has an appropriate legal basis and complies with internal policies and applicable requirements.

8. Policy Updates
The platform owner may publish an updated privacy policy, and users may be required to review or accept the updated version.

9. Contact
Privacy questions should be directed to the organization's administrator or designated privacy contact."""
    }
}

class LegalUpdateRequest(BaseModel):
    title_ar: str = Field(min_length=1, max_length=200)
    title_en: str = Field(min_length=1, max_length=200)
    content_ar: str = Field(min_length=1)
    content_en: str = Field(min_length=1)
    is_published: bool = True

class LegalAcceptRequest(BaseModel):
    document_type: str = Field(pattern="^(terms|privacy)$")
    version: int = Field(ge=1)

def _get_or_create(db: Session, document_type: str) -> LegalDocument:
    document = db.query(LegalDocument).filter(LegalDocument.document_type == document_type).first()
    if document:
        return document
    default = DEFAULTS[document_type]
    document = LegalDocument(document_type=document_type, title_ar=default["title_ar"], title_en=default["title_en"], content_ar=default["content_ar"], content_en=default["content_en"], version=1, is_published=True, published_at=datetime.now(timezone.utc))
    db.add(document); db.commit(); db.refresh(document)
    return document

def _serialize(document: LegalDocument) -> dict:
    return {"id":document.id,"document_type":document.document_type,"title_ar":document.title_ar,"title_en":document.title_en,"content_ar":document.content_ar,"content_en":document.content_en,"version":document.version,"is_published":document.is_published,"published_at":document.published_at,"updated_at":document.updated_at}

def _require_platform_admin(current_user: User) -> User:
    if not (current_user.is_platform_admin or current_user.is_superuser):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the system administrator can manage legal documents.")
    return current_user

@router.get("")
def list_legal_documents(db: Session = Depends(get_db)):
    return {"success":True,"data":[_serialize(_get_or_create(db,"terms")),_serialize(_get_or_create(db,"privacy"))]}

@router.get("/acceptance/status")
def legal_acceptance_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result={}
    for document_type in ("terms","privacy"):
        document=_get_or_create(db,document_type)
        accepted=db.query(LegalAcceptance).filter(LegalAcceptance.user_id==current_user.id,LegalAcceptance.document_type==document_type,LegalAcceptance.document_version==document.version).first() is not None
        result[document_type]={"version":document.version,"accepted":accepted}
    return {"success":True,"data":result}

@router.post("/accept")
def accept_legal_document(payload:LegalAcceptRequest,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    document=_get_or_create(db,payload.document_type)
    if payload.version != document.version:
        raise HTTPException(status_code=409,detail="This legal document version is no longer current.")
    existing=db.query(LegalAcceptance).filter(LegalAcceptance.user_id==current_user.id,LegalAcceptance.document_type==payload.document_type,LegalAcceptance.document_version==payload.version).first()
    if not existing:
        db.add(LegalAcceptance(user_id=current_user.id,document_type=payload.document_type,document_version=payload.version)); db.commit()
    return {"success":True,"data":{"document_type":payload.document_type,"version":payload.version,"accepted":True}}

@router.get("/admin/{document_type}")
def get_admin_legal_document(document_type: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if document_type not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Legal document not found")
    _require_platform_admin(current_user)
    return {"success": True, "data": _serialize(_get_or_create(db, document_type))}

@router.get("/{document_type}")
def get_legal_document(document_type: str, db: Session = Depends(get_db)):
    if document_type not in DEFAULTS:
        raise HTTPException(status_code=404, detail="Legal document not found")
    document = _get_or_create(db, document_type)
    if not document.is_published:
        raise HTTPException(status_code=404, detail="Legal document is not published")
    return {"success": True, "data": _serialize(document)}

@router.put("/{document_type}")
def update_legal_document(document_type:str,payload:LegalUpdateRequest,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    if document_type not in DEFAULTS: raise HTTPException(status_code=404,detail="Legal document not found")
    _require_platform_admin(current_user)
    document=_get_or_create(db,document_type)
    document.title_ar=payload.title_ar.strip(); document.title_en=payload.title_en.strip(); document.content_ar=payload.content_ar; document.content_en=payload.content_en; document.version+=1; document.is_published=payload.is_published; document.updated_by=current_user.id; document.published_at=datetime.now(timezone.utc) if payload.is_published else None
    db.commit(); db.refresh(document)
    return {"success":True,"message":"Legal document updated.","data":_serialize(document)}
