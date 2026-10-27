import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Building2, Loader2, Save, Search, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import client from "@/shared/api/client";
import i18n from "@/shared/i18n/i18n";
import { Button } from "@/components/ui/button";
import { setCompanyDateFormat } from "@/utils/format-date";

type Company = { id:number; name:string };
type Setting = { key:string; module:string; category:string; type:"bool"|"int"|"number"|"string"|"enum"; default:any; value:any; label:string; choices:string[]|null; status:"runtime"|"catalog" };
type Payload = { company_id:number; company_name:string; categories:string[]; settings:Setting[] };

function getInitialCompanyId(): number {
  try {
    const stored = Number(window.localStorage.getItem("company_id"));
    return Number.isSafeInteger(stored) && stored > 0 ? stored : 0;
  } catch {
    return 0;
  }
}

const categoryAr:Record<string,string> = {
  General:"الإعدادات العامة", Accounting:"المحاسبة", Taxes:"الضرائب والفاتورة الإلكترونية",
  Sales:"المبيعات والعملاء", Purchasing:"المشتريات والموردون", Inventory:"المخزون والمستودعات",
  "Human Resources":"الموارد البشرية والحضور والرواتب", Approvals:"الموافقات ودورة العمل",
  "Point of Sale":"نقاط البيع", Manufacturing:"التصنيع", CRM:"إدارة العملاء",
  Integrations:"التكاملات الخارجية", "Messaging & Notifications":"الرسائل والإشعارات", Reporting:"التقارير والتصدير", "Security & Audit":"الأمان والمراجعة"
};
const moduleAr:Record<string,string> = {
  general:"عام", accounting:"المحاسبة", taxes:"الضرائب", "egyptian-einvoice":"الفاتورة الإلكترونية",
  sales:"المبيعات", purchasing:"المشتريات", inventory:"المخزون", hr:"الموارد البشرية",
  approvals:"الموافقات", pos:"نقاط البيع", manufacturing:"التصنيع", crm:"إدارة العملاء", reports:"التقارير",
  integrations:"التكاملات", audit:"المراجعة"
};

export default function CompanyPolicySettingsPage({ categoryFilter }: { categoryFilter?: string } = {}) {
  const isArabic = i18n.resolvedLanguage?.startsWith("ar") ?? true;
  const [companies,setCompanies] = useState<Company[]>([]);
  const [companyId,setCompanyId] = useState<number>(getInitialCompanyId());
  const [payload,setPayload] = useState<Payload|null>(null);
  const [values,setValues] = useState<Record<string,any>>({});
  const [searchParams] = useSearchParams();
  const [activeCategory,setActiveCategory] = useState(() => categoryFilter || searchParams.get("category") || "General");
  const [loading,setLoading] = useState(true);
  const [saving,setSaving] = useState(false);
  const [search,setSearch] = useState("");
  const [statusFilter,setStatusFilter] = useState<"all"|"runtime"|"catalog">("all");

  useEffect(() => {
    client.get<Company[]>("/companies?active_only=true").then(({data}) => {
      setCompanies(data);
      const preferred = data.some(c=>c.id===companyId) ? companyId : (data[0]?.id ?? 0);
      setCompanyId(preferred);
    }).catch((e:any)=>toast.error(e?.response?.data?.detail ?? (isArabic ? "تعذر تحميل الشركات" : "Unable to load companies")))
      .finally(()=>setLoading(false));
  }, []);

  useEffect(() => {
    const requestedCategory = searchParams.get("category");
    if (categoryFilter) { setActiveCategory(categoryFilter); return; }
    if (requestedCategory) setActiveCategory(requestedCategory);
  }, [searchParams, categoryFilter]);

  useEffect(() => {
    if (!companyId) { setPayload(null); return; }
    setLoading(true);
    client.get<Payload>("/company-settings",{params:{company_id:companyId}})
      .then(({data}) => {
        setPayload(data);
        setValues(Object.fromEntries(data.settings.map(s=>[s.key,s.value])));
        const companyDateFormat = data.settings.find(s=>s.key==="general.date_format")?.value;
        setCompanyDateFormat(companyId, companyDateFormat);
        if (!categoryFilter && !data.categories.includes(activeCategory)) setActiveCategory(data.categories[0] || "General");
      })
      .catch((e:any)=>toast.error(e?.response?.data?.detail ?? (isArabic ? "تعذر تحميل سياسات الشركة" : "Unable to load company settings")))
      .finally(()=>setLoading(false));
  }, [companyId]);

  const visibleSettings = useMemo(()=>{const q=search.trim().toLocaleLowerCase();return (payload?.settings??[]).filter(s=>s.category===activeCategory).filter(s=>statusFilter==="all"||s.status===statusFilter).filter(s=>!q||[s.label,s.key,s.module,categoryAr[s.category]??s.category,moduleAr[s.module]??s.module].some(v=>v.toLocaleLowerCase().includes(q))).sort((a,b)=>Number(b.status==="runtime")-Number(a.status==="runtime")||a.label.localeCompare(b.label,"ar"));},[payload,activeCategory,search,statusFilter]);
  const setValue=(key:string,value:any)=>setValues(old=>({...old,[key]:value}));

  async function save() {
    if (!companyId || !payload) return;
    try {
      setSaving(true);
      const changed = Object.fromEntries(payload.settings.filter(s=>values[s.key]!==s.value).map(s=>[s.key,values[s.key]]));
      if (!Object.keys(changed).length) { toast.success(isArabic ? "لا توجد تغييرات للحفظ" : "No changes to save"); return; }
      await client.put("/company-settings",{settings:changed},{params:{company_id:companyId}});
      const {data}=await client.get<Payload>("/company-settings",{params:{company_id:companyId}});
      setPayload(data);
      setValues(Object.fromEntries(data.settings.map(s=>[s.key,s.value])));
      const companyDateFormat = data.settings.find(s=>s.key==="general.date_format")?.value;
      setCompanyDateFormat(companyId, companyDateFormat);
      toast.success(isArabic ? "تم حفظ سياسات الشركة" : "Company settings saved");
    } catch(e:any) { toast.error(e?.response?.data?.detail?.message ?? e?.response?.data?.detail ?? (isArabic ? "تعذر حفظ السياسات" : "Unable to save settings")); }
    finally { setSaving(false); }
  }

  function renderControl(s:Setting) {
    const value=values[s.key] ?? s.default;
    if (s.type==="bool") return <button type="button" role="switch" aria-checked={Boolean(value)} onClick={()=>setValue(s.key,!value)} className={`relative h-7 w-12 rounded-full transition ${value?"bg-primary":"bg-muted"}`}><span className={`absolute top-1 size-5 rounded-full bg-white shadow transition-all ${value?"right-1":"right-6"}`}/></button>;
    if (s.type==="enum") return <select value={String(value)} onChange={e=>setValue(s.key,e.target.value)} className="h-10 w-full rounded-lg border bg-background px-3">{(s.choices??[]).map(c=><option key={c} value={c}>{c}</option>)}</select>;
    if (s.type==="int"||s.type==="number") return <input type="number" step={s.type==="int"?"1":"0.01"} value={value} onChange={e=>setValue(s.key,s.type==="int"?Number.parseInt(e.target.value||"0",10):Number(e.target.value||"0"))} className="h-10 w-full rounded-lg border bg-background px-3"/>;
    return <input type="text" maxLength={200} value={String(value)} onChange={e=>setValue(s.key,e.target.value)} className="h-10 w-full rounded-lg border bg-background px-3"/>;
  }

  if (loading && !payload) return <div className="flex min-h-[50vh] items-center justify-center"><Loader2 className="size-7 animate-spin"/></div>;
  return <main className={categoryFilter ? "w-full space-y-4" : "mx-auto w-full max-w-[1500px] space-y-6 p-4 md:p-6"} dir={i18n.resolvedLanguage?.startsWith("ar") ? "rtl" : "ltr"}>
    {!categoryFilter && <header className="rounded-3xl bg-gradient-to-l from-slate-950 via-blue-950 to-blue-700 p-6 text-white md:p-8">
      <Link to="/settings" className="inline-flex items-center gap-2 text-sm text-blue-100"><ArrowRight className="size-4"/>{isArabic ? "الرجوع للإعدادات العامة" : "Back to general settings"}</Link>
      <div className="mt-4 flex items-center gap-3"><span className="rounded-xl bg-white/10 p-3"><SlidersHorizontal className="size-6"/></span><div><h1 className="text-2xl font-black md:text-3xl">{isArabic ? "سياسات وإعدادات الشركة" : "Company policies and settings"}</h1><p className="mt-2 text-sm leading-6 text-blue-100">{isArabic ? "خصص طريقة تشغيل كل موديول لهذه الشركة دون تعديل الكود. الإعدادات ذات حالة «كتالوج» تحتاج استكمال ربطها بسير العمل قبل أن تغيّر نتائج المعاملات." : "Configure how each module operates for this company. Catalog settings still need workflow integration before they affect transactions."}</p></div></div>
      <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:items-center"><Building2 className="size-5"/><label htmlFor="company-select" className="text-sm">{isArabic ? "الشركة" : "Company"}</label><select id="company-select" value={companyId||""} onChange={e=>{const id=Number(e.target.value);setCompanyId(id);if(id)localStorage.setItem("company_id",String(id));}} className="h-11 min-w-60 rounded-xl border border-white/20 bg-white px-3 text-slate-900">{companies.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select><div className="text-xs text-blue-100">{isArabic ? "الإعدادات محفوظة لكل شركة بصورة مستقلة" : "Settings are isolated per company"}</div></div>

      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4"><div className="rounded-xl border border-white/15 bg-white/10 p-3"><div className="text-xs text-blue-100">{isArabic ? "إجمالي السياسات" : "Total settings"}</div><div className="mt-1 text-2xl font-black">{payload?.settings.length ?? 0}</div></div><div className="rounded-xl border border-emerald-200/30 bg-emerald-400/10 p-3"><div className="text-xs text-emerald-100">{isArabic ? "مرتبطة بسير العمل" : "Runtime enabled"}</div><div className="mt-1 text-2xl font-black">{payload?.settings.filter(s=>s.status==="runtime").length ?? 0}</div></div><div className="rounded-xl border border-amber-200/30 bg-amber-400/10 p-3"><div className="text-xs text-amber-100">{isArabic ? "تحتاج ربطًا تشغيليًا" : "Needs integration"}</div><div className="mt-1 text-2xl font-black">{payload?.settings.filter(s=>s.status==="catalog").length ?? 0}</div></div><div className="rounded-xl border border-white/15 bg-white/10 p-3"><div className="text-xs text-blue-100">{isArabic ? "تغييرات غير محفوظة" : "Unsaved changes"}</div><div className="mt-1 text-2xl font-black">{payload?.settings.filter(s=>values[s.key]!==s.value).length ?? 0}</div></div></div>
    </header>}
    <div className={categoryFilter ? "grid gap-4" : "grid gap-5 lg:grid-cols-[260px_minmax(0,1fr)]"}>
      {!categoryFilter && <nav className="h-fit space-y-1 rounded-2xl border bg-card p-3">{(payload?.categories??[]).map(c=><button key={c} onClick={()=>setActiveCategory(c)} className={`w-full rounded-xl px-4 py-3 text-right text-sm font-semibold transition ${activeCategory===c?"bg-primary text-primary-foreground":"hover:bg-muted"}`}>{isArabic ? (categoryAr[c]??c) : c}<span className="mt-1 block text-xs opacity-70">{payload?.settings.filter(s=>s.category===c).length} {isArabic ? "إعداد" : "settings"}</span></button>)}</nav>}
      <section className="min-w-0 space-y-4">
        <div className="flex flex-col justify-between gap-3 rounded-2xl border bg-card p-5 sm:flex-row sm:items-center"><div><h2 className="text-xl font-black">{isArabic ? (categoryAr[activeCategory]??activeCategory) : activeCategory}</h2><p className="mt-1 text-sm text-muted-foreground">{isArabic ? "تغيّر السياسة هنا يؤثر على الشركة المختارة فقط، ولا يمنح صلاحيات إضافية للمستخدمين." : "Changes apply only to the selected company and do not grant additional user permissions."}</p></div><Button onClick={()=>void save()} disabled={saving||!payload||!payload.settings.some(s=>values[s.key]!==s.value)} className="gap-2"><Save className="size-4"/>{saving ? (isArabic ? "جارٍ الحفظ" : "Saving") : payload?.settings.some(s=>values[s.key]!==s.value) ? (isArabic ? "حفظ التغييرات" : "Save changes") : (isArabic ? "لا توجد تغييرات" : "No changes")}</Button></div>
        <div className="grid gap-3 rounded-2xl border bg-card p-4 md:grid-cols-[minmax(0,1fr)_220px]"><label className="relative block"><Search className="pointer-events-none absolute right-3 top-3 size-4 text-muted-foreground"/><input aria-label={isArabic ? "بحث في الإعدادات" : "Search settings"} value={search} onChange={e=>setSearch(e.target.value)} placeholder={isArabic ? "ابحث باسم الإعداد أو المفتاح أو الموديول..." : "Search settings, keys, or modules..."} className="h-10 w-full rounded-xl border bg-background pr-10 pl-3 text-sm"/></label><select aria-label={isArabic ? "تصفية حالة الربط" : "Filter integration status"} value={statusFilter} onChange={e=>setStatusFilter(e.target.value as "all"|"runtime"|"catalog")} className="h-10 rounded-xl border bg-background px-3 text-sm"><option value="all">{isArabic ? "كل الحالات" : "All statuses"}</option><option value="runtime">{isArabic ? "مفعّل في النظام فقط" : "Runtime enabled only"}</option><option value="catalog">{isArabic ? "يحتاج ربطًا تشغيليًا فقط" : "Needs integration only"}</option></select></div>
        <div className="flex items-center justify-between px-1 text-xs text-muted-foreground"><span>{isArabic ? "عدد النتائج" : "Results"}: {visibleSettings.length}</span><button type="button" onClick={()=>{setSearch("");setStatusFilter("all");}} className="underline underline-offset-4">{isArabic ? "مسح البحث والتصفية" : "Clear search and filters"}</button></div>
        {visibleSettings.length===0&&<div className="rounded-2xl border border-dashed p-8 text-center text-sm text-muted-foreground">{isArabic ? "لا توجد إعدادات مطابقة للبحث والتصفية الحالية." : "No settings match the current search and filters."}</div>}
        {visibleSettings.map(s=><article key={s.key} className="grid gap-4 rounded-2xl border bg-card p-5 md:grid-cols-[minmax(0,1fr)_220px] md:items-center"><div><div className="flex flex-wrap items-center gap-2"><h3 className="font-bold">{s.label}</h3><span className={`rounded-full px-2 py-1 text-[11px] ${s.status==="runtime"?"bg-emerald-100 text-emerald-800":"bg-amber-100 text-amber-800"}`}>{s.status==="runtime" ? (isArabic ? "مفعّل في النظام" : "Runtime enabled") : (isArabic ? "كتالوج — يحتاج ربط تشغيلي" : "Catalog — integration needed")}</span></div><p className="mt-2 text-xs text-muted-foreground">{isArabic ? "الموديول" : "Module"}: {isArabic ? (moduleAr[s.module]??s.module) : s.module}</p><code className="mt-1 block break-all text-[11px] text-muted-foreground">{s.key}</code></div><div className="flex items-center justify-between gap-4">{renderControl(s)}</div></article>)}
        <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 text-sm leading-6 text-blue-950"><ShieldCheck className="mb-2 size-5"/>الإعدادات الحساسة مثل بيانات الدخول ومفاتيح API لا تُحفظ هنا؛ يجب إدارتها من خزنة التكاملات. لا يتم تغيير المستندات المرحلة سابقًا عند تعديل سياسة افتراضية.</div>
      </section>
    </div>
  </main>;
}
