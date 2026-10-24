import { Link } from "react-router-dom";
import { BarChart3, Calculator, Boxes, ShoppingCart, Users, Building2, Hotel, FileSpreadsheet, ArrowLeft, Clock3 } from "lucide-react";

type ReportLink = { name: string; path: string; available: boolean };
type ReportGroup = { id: string; title: string; description: string; icon: typeof Calculator; reports: ReportLink[] };

// Only reports with a concrete route and known page are enabled. A card must not imply
// that a report is implemented when its route currently falls through to the wildcard page.
const groups: ReportGroup[] = [
  { id:"accounting", title:"تقارير المحاسبة", description:"الأستاذ العام، ميزان المراجعة، القوائم المالية، الخزينة ومراكز التكلفة.", icon:Calculator, reports:[
    {name:"القوائم والتقارير المالية",path:"/reports/financial",available:true},
    {name:"ميزان المراجعة والأستاذ العام",path:"/reports/ledger",available:false},
    {name:"الخزينة والبنوك",path:"/reports/treasury",available:false}
  ]},
  { id:"commerce", title:"تقارير التجارة وCommercialERP", description:"المبيعات والمشتريات والعملاء والموردون والربحية وحركة المستندات.", icon:ShoppingCart, reports:[
    {name:"المبيعات والعملاء",path:"/reports/sales",available:false},
    {name:"المشتريات والموردون",path:"/reports/purchasing",available:false},
    {name:"تحليل الربحية",path:"/reports/profitability",available:false}
  ]},
  { id:"inventory", title:"تقارير المخزون", description:"الأرصدة والحركات والتحويلات والجرد والأصناف الراكدة.", icon:Boxes, reports:[
    {name:"أرصدة وحركة المخزون",path:"/reports/inventory",available:false},
    {name:"الجرد والتحويلات",path:"/reports/stock-counts",available:false}
  ]},
  { id:"hr", title:"تقارير الموارد البشرية", description:"الحضور والإجازات والرواتب والقوى العاملة.", icon:Users, reports:[
    {name:"الحضور والإجازات",path:"/reports/hr/attendance",available:false},
    {name:"الرواتب",path:"/reports/hr/payroll",available:false}
  ]},
  { id:"hospitality", title:"تقارير الفنادق والإيجارات", description:"الإيرادات والإشغال وعقود الإيجار والاستحقاقات.", icon:Hotel, reports:[
    {name:"إيرادات الفنادق",path:"/reports/hospitality",available:false},
    {name:"الإيجارات والاستحقاقات",path:"/reports/leasing",available:false}
  ]},
  { id:"shipping", title:"تقارير الشحن", description:"موقف شركات الشحن والتسويات والمستحقات غير المسواة.", icon:Boxes, reports:[
    {name:"موقف شركات الشحن والتسويات",path:"/reports/shipping/reconciliation",available:true}
  ]},
  { id:"management", title:"تقارير الإدارة والمؤسسة", description:"مؤشرات الأداء والتدقيق والتشغيل ومقارنة الفروع.", icon:Building2, reports:[
    {name:"التحليل الذكي وجدولة التقارير",path:"/reports/analysis",available:true},
    {name:"سجل التدقيق",path:"/reports/audit",available:false}
  ]}
];

export default function ReportCenterPage() {
 return <main className="mx-auto w-full max-w-[1600px] space-y-6 p-5 md:p-8" dir="rtl">
  <header className="rounded-3xl bg-gradient-to-l from-slate-950 via-blue-900 to-sky-700 p-7 text-white shadow-lg md:p-9">
   <div className="flex items-center gap-3"><span className="rounded-2xl bg-white/10 p-3"><BarChart3 className="size-7"/></span><div><p className="text-sm text-blue-100">PrimeERP · مركز التقارير</p><h1 className="mt-1 text-3xl font-black">جميع تقارير النظام في مكان واحد</h1></div></div>
   <p className="mt-4 max-w-3xl leading-7 text-blue-50">التقارير منظمة حسب الموديول المصدر. لا يتم تفعيل رابط التقرير إلا عند وجود صفحة تشغيلية معروفة؛ وتظل صلاحيات الوصول إلى البيانات مسؤولية الخادم أيضًا.</p>
   <Link to="/reports/analysis" className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 font-bold text-blue-950 hover:bg-blue-50"><FileSpreadsheet className="size-4"/> التحليل الذكي وجدولة التقارير <ArrowLeft className="size-4"/></Link>
  </header>
  <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">{groups.map(g=>{const Icon=g.icon;return <article key={g.id} className="rounded-2xl border bg-card p-5 shadow-sm">
   <div className="flex items-start gap-3"><span className="rounded-xl bg-primary/10 p-3 text-primary"><Icon className="size-5"/></span><div><h2 className="text-lg font-extrabold">{g.title}</h2><p className="mt-1 text-sm leading-6 text-muted-foreground">{g.description}</p></div></div>
   <div className="mt-4 space-y-2">{g.reports.map(r=>r.available
    ? <Link key={r.path} to={r.path} className="flex items-center justify-between rounded-xl border px-3 py-2.5 text-sm hover:bg-muted"><span>{r.name}</span><ArrowLeft className="size-4 text-muted-foreground"/></Link>
    : <div key={r.path} aria-disabled="true" className="flex items-center justify-between gap-3 rounded-xl border border-dashed px-3 py-2.5 text-sm text-muted-foreground"><span>{r.name}</span><span className="inline-flex shrink-0 items-center gap-1 text-xs"><Clock3 className="size-3.5"/>قيد التنفيذ</span></div>
   )}</div>
  </article>})}</section>
  <p className="rounded-xl border border-amber-300/50 bg-amber-50 p-4 text-sm leading-6 text-amber-950 dark:bg-amber-950/20 dark:text-amber-100">التقارير المعطلة هنا لم يتم ربطها بعد بصفحات تشغيلية مؤكدة في هذا الفرع. تم تعطيل التنقل إليها بدلًا من إرسال المستخدم إلى صفحة غير موجودة. قبل تفعيل أي تقرير جديد، يجب استكمال الخدمة والاختبارات وصلاحيات الموديول والشركة.</p>
 </main>
}