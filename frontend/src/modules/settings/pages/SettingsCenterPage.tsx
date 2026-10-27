import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Settings, Building2, Calculator, ShoppingCart, Boxes, Users, Workflow, MessageCircle, BarChart3, ShieldCheck, Plug, Receipt, Store, Factory, ContactRound, SlidersHorizontal } from "lucide-react";
import { useTranslation } from "react-i18next";
import SettingsPage from "./SettingsPage";
import CompanyPolicySettingsPage from "./CompanyPolicySettingsPage";

const sections = [
 {id:"General",title:"الإعدادات العامة",english:"General",desc:"بيانات الشركة واللغة والتاريخ والمنطقة الزمنية والعملة.",icon:Building2},
 {id:"Accounting",title:"المحاسبة",english:"Accounting",desc:"الفترات المالية والحسابات وسياسات الترحيل.",icon:Calculator},
 {id:"Taxes",title:"الضرائب والفاتورة الإلكترونية",english:"Taxes & e-Invoicing",desc:"الضرائب والإقرارات والفوترة الإلكترونية.",icon:Receipt},
 {id:"Sales",title:"المبيعات والعملاء",english:"Sales & Customers",desc:"التسعير والخصومات والائتمان والمبيعات.",icon:ShoppingCart},
 {id:"Purchasing",title:"المشتريات والموردون",english:"Purchasing & Suppliers",desc:"المشتريات والاعتمادات وسياسات الموردين.",icon:Store},
 {id:"Inventory",title:"المخزون والمستودعات",english:"Inventory & Warehouses",desc:"التقييم والحجز والجرد وإعادة الطلب.",icon:Boxes},
 {id:"Human Resources",title:"الموارد البشرية والحضور والرواتب",english:"HR, Attendance & Payroll",desc:"البصمة والحضور والإجازات والرواتب والاعتماد.",icon:Users},
 {id:"Approvals",title:"الموافقات وسير العمل",english:"Approvals & Workflow",desc:"مسارات الاعتماد والتفويض والتصعيد.",icon:Workflow},
 {id:"Point of Sale",title:"نقاط البيع ودرج النقدية",english:"POS & Cash Drawer",desc:"إعدادات نقاط البيع والوردية ودرج النقدية.",icon:Store},
 {id:"Manufacturing",title:"التصنيع",english:"Manufacturing",desc:"أوامر الإنتاج وقوائم المواد والتكاليف.",icon:Factory},
 {id:"CRM",title:"إدارة العملاء",english:"CRM",desc:"مراحل الفرص والعملاء والمتابعة.",icon:ContactRound},
 {id:"Integrations",title:"التكاملات الخارجية",english:"Integrations",desc:"الأنظمة الخارجية والربط والمزامنة.",icon:Plug},
 {id:"Messaging & Notifications",title:"الرسائل وWhatsApp",english:"Messages & WhatsApp",desc:"قوالب الرسائل والمجموعات والتنبيهات.",icon:MessageCircle},
 {id:"Reporting",title:"التقارير والتصدير",english:"Reports & Export",desc:"خيارات التقارير والتصدير والجدولة.",icon:BarChart3},
 {id:"Security & Audit",title:"الأمان والمراجعة",english:"Security & Audit",desc:"الصلاحيات والجلسات وسجل التدقيق.",icon:ShieldCheck},
];

export default function SettingsCenterPage() {
 const [searchParams,setSearchParams] = useSearchParams();
 const { i18n } = useTranslation();
 const isArabic = i18n.resolvedLanguage?.startsWith("ar") ?? true;
 const active = searchParams.get("category") || "General";
 const selected = useMemo(() => sections.find((section) => section.id === active) ?? sections[0], [active]);
 const Icon = selected.icon;
 const selectSection = (id:string) => setSearchParams({category:id}, {replace:false});
 return <div className="mx-auto w-full max-w-[1700px] space-y-5">
   <header className="overflow-hidden rounded-3xl bg-gradient-to-l from-slate-950 via-indigo-900 to-blue-700 p-6 text-white shadow-lg md:p-8">
    <div className="flex items-center gap-3"><span className="rounded-2xl bg-white/10 p-3"><Settings className="size-7"/></span><div><p className="text-sm text-indigo-100">PrimeERP · {isArabic ? "مركز التحكم" : "Control Center"}</p><h1 className="mt-1 text-2xl font-black md:text-3xl">{isArabic ? "إعدادات النظام" : "System Settings"}</h1></div></div>
    <p className="mt-3 max-w-3xl text-sm leading-7 text-indigo-50">{isArabic ? "اختر الموديول من القائمة الجانبية لعرض إعداداته فقط. يتم الاحتفاظ بإعدادات كل مجال في قسم مستقل." : "Choose a module from the sidebar to display only its settings. Each area has its own dedicated settings section."}</p>
   </header>
   <div className="grid min-h-[68vh] gap-5 lg:grid-cols-[270px_minmax(0,1fr)]">
    <aside className="h-fit rounded-2xl border bg-card p-3 shadow-sm lg:sticky lg:top-24">
      <div className="flex items-center gap-2 px-3 pb-3 pt-2 text-xs font-bold text-muted-foreground"><SlidersHorizontal className="size-4"/>{isArabic ? "إعدادات الموديولات" : "Module settings"}</div>
      <nav aria-label={isArabic ? "أقسام الإعدادات" : "Settings sections"} className="space-y-1">
       {sections.map((section) => { const SectionIcon = section.icon; const isActive = selected.id === section.id; return <button key={section.id} type="button" onClick={() => selectSection(section.id)} aria-current={isActive ? "page" : undefined} className={["flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-start text-sm transition-colors", isActive ? "bg-primary text-primary-foreground shadow-sm" : "text-foreground hover:bg-muted"].join(" ")}><SectionIcon className="size-4 shrink-0"/><span className="min-w-0 flex-1 truncate">{isArabic ? section.title : section.english}</span></button> })}
      </nav>
    </aside>
    <section className="min-w-0 rounded-2xl border bg-card p-3 shadow-sm sm:p-5">
      <div className="mb-5 flex items-start gap-3 border-b pb-4"><span className="rounded-xl bg-primary/10 p-3 text-primary"><Icon className="size-5"/></span><div><h2 className="text-lg font-extrabold">{isArabic ? selected.title : selected.english}</h2><p className="mt-1 text-sm leading-6 text-muted-foreground">{isArabic ? selected.desc : "Configure policies and defaults for this module."}</p></div></div>
      <div className="min-w-0">{selected.id === "General" ? <SettingsPage /> : <CompanyPolicySettingsPage key={selected.id} categoryFilter={selected.id} />}</div>
    </section>
   </div>
 </div>;
}
