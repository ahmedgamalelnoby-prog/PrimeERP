import { CalendarDays, RefreshCw } from "lucide-react";

import {
  BusinessUnitsSummary,
  QuickActions,
  RecentActivities,
  RevenueOverview,
  StatisticCard,
} from "../components/dashboard";

import { dashboardStatistics } from "../data/dashboard.data";

export default function DashboardPage() {
  const currentDate = new Intl.DateTimeFormat("ar-EG", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date());

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6">
      <header className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
            لوحة التحكم
          </h1>

          <p className="mt-1 text-sm text-muted-foreground">
            مرحبًا بك، إليك ملخص الأداء المالي والتشغيلي.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex items-center gap-2 rounded-xl border bg-card px-4 py-2 text-sm shadow-sm">
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
            <span>{currentDate}</span>
          </div>

          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-xl border bg-card px-4 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-muted"
          >
            <RefreshCw className="h-4 w-4" />
            تحديث
          </button>
        </div>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {dashboardStatistics.map((statistic) => (
          <StatisticCard
            key={statistic.id}
            statistic={statistic}
          />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <RevenueOverview />
        <BusinessUnitsSummary />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <QuickActions />
        <RecentActivities />
      </section>
    </div>
  );
}
