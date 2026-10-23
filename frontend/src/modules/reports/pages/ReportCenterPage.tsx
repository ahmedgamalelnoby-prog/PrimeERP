import { Link } from "react-router-dom";
import { BarChart3, Calculator, Boxes, ShoppingCart, Users, Building2, Hotel, FileSpreadsheet, ArrowLeft } from "lucide-react";

const groups = [
  { id:"accounting", title:"تقارير المحاسبة", description:"الأستاذ العام، ميزان المراجعة، القوائم المالية، الخزينة ومراكز التكلفة.", icon:Calculator, reports:[["القوائم والتقارير المالية","/reports/financial"],["ميزان المراجعة والأستاذ العام","/reports/ledger"],["الخزينة والبنوك","/reports/treasury"]] },
  { id:"commerce", title:"تقارير التجارة وCommercialERP", description:"المبيعات والمشتريات والعملاء والموردون والربحية وحركة المستندات.", icon:ShoppingCart, reports:[["المبيعات والعملاء","/reports/sales"],["المشتريات والموردون","/reports/purchasing"],["تحليل الربحية","/reports/profitability"]] },
  { id:"inventory", title:"تقارير المخزون", description:"الأرصدة والحركات والتحويلات والجرد والأصناف الراكدة.", icon:Boxes, reports:[["أرصدة وحركة المخزون","/reports/inventory"],["الجرد والتحويلات","/reports/stock-counts"]] },
  { id:"hr", title:"تقارير الموارد البشرية", description:"الحضور والإجازات والرواتب والقوى العاملة.", icon:Users, reports:[["الحضور والإجازات","/reports/hr/attendance"],["الرواتب","/reports/hr/payroll"]] },
  { id:"hospitality", title:"تقارير الفنادق والإيجارات", description:"الإيرادات والإشغال وعقود الإيجار والاستحقاقات.", icon:Hotel, reports:[["إيرادات الفنادق","/reports/hospitality"],["الإيجارات والاستحقاقات","/reports/leasing"]] },
  { id:"management", title:"تقارير الإدارة والمؤسسة", description:"مؤشرات الأداء والتدقيق والتشغيل ومقارنة الفروع.", icon:Building2, reports:[["لوحة مؤشرات الإدارة","/reports/management"],["سجل التدقيق","/reports/audit"]] },
];
export default function ReportCenterPage() {
 return <main className="mx-auto w-full max-w-[1600px] space-y-6 p-5 md:p-8" dir="rtl">
  <header className="rounded-3xl bg-gradient-to-l from-slate-950 via-blue-900 to-sky-700 p-7 text-white shadow-lg md:p-9">
   <div className="flex items-center gap-3"><span className="rounded-2xl bg-white/10 p-3"><BarChart3 className="size-7"/></span><div><p className="text-sm text-blue-100">PrimeERP · مركز التقارير</p><h1 className="mt-1 text-3xl font-black">جميع تقارير النظام في مكان واحد</h1></div></div>
   <p className="mt-4 max-w-3xl leading-7 text-blue-50">التقارير منظمة حسب الموديول المصدر، مع فصل واضح بين المجالات وإمكانية التوسع. الوصول الفعلي لكل تقرير يجب أن يخضع لصلاحيات المستخدم وبيانات شركته.</p>
   <Link to="/reports/analysis" className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 font-bold text-blue-950 hover:bg-blue-50"><FileSpreadsheet className="size-4"/> التحليل الذكي وجدولة التقارير <ArrowLeft className="size-4"/></Link>
  </header>
  <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">{groups.map(g=>{const Icon=g.icon;return <article key={g.id} className="rounded-2xl border bg-card p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
   <div className="flex items-start gap-3"><span className="rounded-xl bg-primary/10 p-3 text-primary"><Icon className="size-5"/></span><div><h2 className="text-lg font-extrabold">{g.title}</h2><p className="mt-1 text-sm leading-6 text-muted-foreground">{g.description}</p></div></div>
   <div className="mt-4 space-y-2">{g.reports.map(([name,path])=><Link key={path} to={path} className="flex items-center justify-between rounded-xl border px-3 py-2.5 text-sm hover:bg-muted"><span>{name}</span><ArrowLeft className="size-4 text-muted-foreground"/></Link>)}</div>
  </article>})}</section>
  <p className="rounded-xl border border-amber-300/50 bg-amber-50 p-4 text-sm leading-6 text-amber-950 dark:bg-amber-950/20 dark:text-amber-100">ملاحظة تنفيذية: الروابط التفصيلية التي لم تُربط بعد بصفحات تقارير تشغيلية ستحتاج إلى استكمال المسارات والخدمات والصلاحيات؛ لا تُعد بطاقة التقرير وحدها تقريرًا منفذًا.</p>
 </main>
}