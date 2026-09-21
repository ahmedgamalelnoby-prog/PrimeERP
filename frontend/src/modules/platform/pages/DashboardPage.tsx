import { useEffect, useMemo, useState } from "react";
import { CalendarDays, RefreshCw } from "lucide-react";

import { BusinessUnitsSummary, QuickActions, RecentActivities, RevenueOverview, StatisticCard } from "../components/dashboard";
import { dashboardStatistics as fallbackStatistics, businessUnits as fallbackBusinessUnits } from "../data/dashboard.data";
import { dashboardApi, type DashboardSummary } from "../api/dashboard.api";

function formatMoney(value: number) {
  return new Intl.NumberFormat("ar-EG", { style: "currency", currency: "EGP", maximumFractionDigits: 0 }).format(value);
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const currentDate = new Intl.DateTimeFormat("ar-EG", { weekday: "long", year: "numeric", month: "long", day: "numeric" }).format(new Date());

  const load = async () => {
    setLoading(true);
    try { setSummary(await dashboardApi.summary()); } finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);

  const statistics = useMemo(() => {
    if (!summary) return fallbackStatistics;
    const change = summary.revenue_previous_month > 0 ? Math.round(((summary.revenue_current_month - summary.revenue_previous_month) / summary.revenue_previous_month) * 100) : 0;
    return fallbackStatistics.map((item) => ({
      ...item,
      value: item.id === 1 ? String(summary.users) : item.id === 2 ? String(summary.companies) : item.id === 3 ? String(summary.branches) : formatMoney(summary.revenue_current_month),
      change: item.id === 4 ? change : item.change,
    }));
  }, [summary]);

  const units = useMemo(() => {
    if (!summary) return fallbackBusinessUnits;
    return fallbackBusinessUnits.map((item) => ({ ...item, value: item.id === 1 ? summary.companies : item.id === 2 ? summary.branches : item.id === 3 ? summary.customers : summary.users }));
  }, [summary]);

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6">
      <header className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div><h1 className="text-2xl font-bold tracking-tight md:text-3xl">لوحة التحكم</h1><p className="mt-1 text-sm text-muted-foreground">مرحبًا بك، إليك ملخص الأداء المالي والتشغيلي.</p></div>
        <div className="flex flex-wrap items-center gap-3"><div className="inline-flex items-center gap-2 rounded-xl border bg-card px-4 py-2 text-sm shadow-sm"><CalendarDays className="h-4 w-4 text-muted-foreground" /><span>{currentDate}</span></div><button type="button" onClick={() => void load()} disabled={loading} className="inline-flex items-center gap-2 rounded-xl border bg-card px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-muted disabled:opacity-60"><RefreshCw className={loading ? "h-4 w-4 animate-spin" : "h-4 w-4"} />{loading ? "جاري التحديث" : "تحديث"}</button></div>
      </header>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{statistics.map((statistic) => <StatisticCard key={statistic.id} statistic={statistic} />)}</section>
      <section className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]"><RevenueOverview /><BusinessUnitsSummary items={units} /></section>
      <section className="grid gap-6 xl:grid-cols-2"><QuickActions /><RecentActivities /></section>
    </div>
  );
}
