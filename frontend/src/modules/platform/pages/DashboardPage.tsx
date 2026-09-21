import { CalendarDays, RefreshCw, Building2, Users, GitBranch } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "react-hot-toast";
import { getDashboardSummary, type DashboardSummary } from "../services/dashboard.service";
import { buildBusinessUnits } from "../data/dashboard.data";
import StatisticCard from "../components/dashboard/StatisticCard";
import BusinessUnitsSummary from "../components/dashboard/BusinessUnitsSummary";
import QuickActions from "../components/dashboard/QuickActions";


function LiveRevenue({ points }: { points: { month: string; revenue: number; expenses: number }[] }) {
  const max = Math.max(1, ...points.flatMap((p) => [p.revenue, p.expenses]));
  return <section className="rounded-2xl border bg-card p-5 shadow-sm"><h2 className="text-lg font-semibold">الإيرادات والمصروفات</h2><p className="mt-1 text-sm text-muted-foreground">من القيود المحاسبية المرحّلة للـtenant الحالي</p><div className="mt-8 flex h-64 items-end gap-3 border-b border-dashed px-2">{points.map((p) => <div key={p.month} className="flex h-full min-w-0 flex-1 items-end justify-center gap-1"><div className="w-2/5 rounded-t-md bg-primary" style={{height: `${Math.max(2, p.revenue / max * 100)}%`}} title={`الإيرادات: ${p.revenue.toLocaleString("ar-EG")}`} /><div className="w-2/5 rounded-t-md bg-muted-foreground/40" style={{height: `${Math.max(2, p.expenses / max * 100)}%`}} title={`المصروفات: ${p.expenses.toLocaleString("ar-EG")}`} /></div>)}</div><div className="mt-3 flex justify-between gap-2 text-xs text-muted-foreground">{points.map((p) => <span key={p.month} className="truncate">{p.month}</span>)}</div></section>;
}

function LiveActivities({ items }: { items: DashboardSummary["recent_activities"] }) {
  const dots: Record<string, string> = { success: "bg-emerald-500", warning: "bg-amber-500", info: "bg-blue-500", danger: "bg-red-500" };
  return <section className="rounded-2xl border bg-card p-5 shadow-sm"><h2 className="text-lg font-semibold">آخر الأنشطة</h2><p className="mt-1 text-sm text-muted-foreground">أحدث العمليات المسجلة فعليًا</p><div className="mt-5 space-y-1">{items.length ? items.map((a) => <div key={a.id} className="flex gap-3 rounded-xl p-3 hover:bg-muted/50"><span className={`mt-2 block h-2.5 w-2.5 shrink-0 rounded-full ${dots[a.status] ?? dots.info}`} /><div className="min-w-0 flex-1"><p className="text-sm font-medium">{a.title}</p><p className="mt-1 text-xs text-muted-foreground">{a.description}</p></div><time className="shrink-0 text-xs text-muted-foreground">{a.time ? new Date(a.time).toLocaleString("ar-EG") : ""}</time></div>) : <p className="py-8 text-center text-sm text-muted-foreground">لا توجد أنشطة مسجلة حتى الآن.</p>}</div></section>;
}

const numberFormatter = new Intl.NumberFormat("ar-EG");

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (manual = false) => {
    manual ? setRefreshing(true) : setLoading(true);
    try { setSummary(await getDashboardSummary()); }
    catch (error) { console.error("Dashboard summary failed", error); toast.error("تعذر تحميل بيانات لوحة التحكم."); }
    finally { manual ? setRefreshing(false) : setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const currentDate = new Intl.DateTimeFormat("ar-EG", { weekday: "long", year: "numeric", month: "long", day: "numeric" }).format(new Date());
  const units = useMemo(() => buildBusinessUnits(summary ?? { users: { total: 0 }, companies: { total: 0 }, branches: { total: 0 } }), [summary]);
  const stats = [
    { id: 1, title: "إجمالي المستخدمين", value: loading ? "—" : numberFormatter.format(summary?.users.total ?? 0), change: 0, changeLabel: `${numberFormatter.format(summary?.users.active ?? 0)} نشط`, icon: Users },
    { id: 2, title: "الشركات", value: loading ? "—" : numberFormatter.format(summary?.companies.total ?? 0), change: 0, changeLabel: `${numberFormatter.format(summary?.companies.active ?? 0)} نشطة`, icon: Building2 },
    { id: 3, title: "الفروع", value: loading ? "—" : numberFormatter.format(summary?.branches.total ?? 0), change: 0, changeLabel: `${numberFormatter.format(summary?.branches.active ?? 0)} نشطة`, icon: GitBranch },
  ];

  return <div className="mx-auto w-full max-w-[1600px] space-y-6">
    <header className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
      <div><p className="text-sm font-semibold text-primary">{summary?.tenant?.name ?? "PrimeERP"}</p><h1 className="text-2xl font-bold tracking-tight md:text-3xl">لوحة التحكم</h1><p className="mt-1 text-sm text-muted-foreground">ملخص مباشر للمؤسسة الحالية.</p></div>
      <div className="flex flex-wrap items-center gap-3"><div className="inline-flex items-center gap-2 rounded-xl border bg-card px-4 py-2 text-sm shadow-sm"><CalendarDays className="h-4 w-4 text-muted-foreground" /><span>{currentDate}</span></div><button type="button" onClick={() => void load(true)} disabled={loading || refreshing} className="inline-flex items-center gap-2 rounded-xl border bg-card px-4 py-2 text-sm font-medium shadow-sm hover:bg-muted disabled:opacity-60"><RefreshCw className={refreshing ? "h-4 w-4 animate-spin" : "h-4 w-4"} />تحديث</button></div>
    </header>
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{stats.map((stat) => <StatisticCard key={stat.id} statistic={stat} />)}</section>
    <section className="grid gap-6 xl:grid-cols-2"><BusinessUnitsSummary units={units} /><QuickActions /></section>
    <section className="grid gap-6 xl:grid-cols-2"><LiveRevenue points={summary?.revenue_overview ?? []} /><LiveActivities items={summary?.recent_activities ?? []} /></section>
    <section className="rounded-2xl border bg-card p-6 shadow-sm"><h2 className="text-lg font-semibold">حالة لوحة التحكم</h2><p className="mt-1 text-sm text-muted-foreground">المؤشرات الأساسية هنا تأتي من قاعدة البيانات ضمن الـtenant الحالي.</p></section>
  </div>;
}