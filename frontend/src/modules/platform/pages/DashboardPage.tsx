import { ArrowUpLeft, CalendarDays, RefreshCw, Sparkles } from "lucide-react";
import { useAuth } from "@/modules/identity/context/AuthContext";
import { BusinessUnitsSummary, QuickActions, RecentActivities, RevenueOverview, StatisticCard } from "../components/dashboard";
import { dashboardStatistics } from "../data/dashboard.data";

export default function DashboardPage() {
  const { user } = useAuth();
  const currentDate = new Intl.DateTimeFormat("ar-EG", { weekday:"long", year:"numeric", month:"long", day:"numeric" }).format(new Date());
  const greeting = user?.full_name ? "مرحبًا " + user.full_name : "مرحبًا بك في PrimeERP";
  return <div className="mx-auto w-full max-w-[1680px] space-y-6">
    <section className="relative overflow-hidden rounded-[28px] bg-slate-950 px-6 py-7 text-white shadow-xl shadow-slate-900/10 sm:px-8">
      <div className="absolute -left-16 -top-20 size-64 rounded-full bg-blue-500/20 blur-3xl"/><div className="absolute -bottom-24 right-20 size-72 rounded-full bg-indigo-500/15 blur-3xl"/>
      <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
        <div><div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-bold text-blue-200"><Sparkles className="size-3.5"/>Executive Workspace</div><h1 className="text-3xl font-black tracking-tight sm:text-4xl">{greeting}</h1><p className="mt-2 max-w-2xl text-sm leading-7 text-slate-300">نظرة موحدة على الأداء المالي والتشغيلي والمبيعات والمخزون والفروع، مع وصول سريع إلى أهم الإجراءات.</p></div>
        <div className="flex flex-wrap gap-2"><div className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-slate-200"><CalendarDays className="size-4"/>{currentDate}</div><button type="button" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-slate-950 hover:bg-slate-100"><RefreshCw className="size-4"/>تحديث البيانات</button></div>
      </div>
    </section>
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{dashboardStatistics.map((statistic)=><StatisticCard key={statistic.id} statistic={statistic}/>)}</section>
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.8fr)_minmax(320px,1fr)]"><RevenueOverview/><BusinessUnitsSummary/></section>
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]"><QuickActions/><RecentActivities/></section>
    <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-5 py-4 text-sm text-slate-500 shadow-sm"><span>الوصول الحالي حسب صلاحيات المستخدم.</span><span className="inline-flex items-center gap-1 font-semibold text-blue-600">استكشف الوحدات <ArrowUpLeft className="size-4"/></span></div>
  </div>;
}
