import { CalendarDays, CheckCircle2, RefreshCw, ShieldCheck, Sparkles, Users, Boxes, CircleDollarSign } from "lucide-react";
import { Link } from "react-router-dom";

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
    <div className="mx-auto w-full max-w-[1600px] space-y-7" dir="rtl">
      <section className="relative overflow-hidden rounded-[28px] bg-gradient-to-l from-[#063f9f] via-[#0968d7] to-[#21a8ef] p-7 text-white shadow-xl shadow-blue-900/10 md:p-9">
        <div className="absolute -left-20 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -right-20 -bottom-24 h-72 w-72 rounded-full bg-cyan-300/10 blur-3xl" />
        <div className="relative flex flex-col justify-between gap-7 lg:flex-row lg:items-end">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-bold">
              <Sparkles className="h-4 w-4" /> PrimeERP Azul
            </span>
            <h1 className="mt-4 text-3xl font-black tracking-tight md:text-4xl">لوحة القيادة</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-blue-50/90">
              رؤية موحدة للأداء المالي والتشغيلي مع وصول سريع إلى الموديولات التي تحتاجها اليوم.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/10 px-4 py-2 text-sm">
              <CalendarDays className="h-4 w-4" /> {currentDate}
            </div>
            <button type="button" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-bold text-blue-700 hover:bg-blue-50">
              <RefreshCw className="h-4 w-4" /> تحديث
            </button>
          </div>
        </div>
        <div className="relative mt-7 grid gap-3 sm:grid-cols-3">
          {[
            ["Platform", "Operational", ShieldCheck],
            ["Modules", "Connected", Boxes],
            ["AI", "Ready", Sparkles],
          ].map(([label, value, Icon]) => (
            <div key={String(label)} className="rounded-2xl border border-white/10 bg-white/[0.08] p-4 backdrop-blur">
              <Icon className="h-5 w-5 text-cyan-200" />
              <div className="mt-3 text-xs text-blue-100/70">{String(label)}</div>
              <div className="mt-1 font-black">{String(value)}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {dashboardStatistics.map((statistic) => (
          <StatisticCard key={statistic.id} statistic={statistic} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <RevenueOverview />
        <BusinessUnitsSummary />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
        <QuickActions />
        <div className="rounded-[24px] border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div><p className="text-xs font-bold uppercase tracking-wider text-blue-600">Prime AI</p><h2 className="mt-1 text-xl font-black">ماذا يحتاج انتباهك؟</h2></div>
            <Sparkles className="h-6 w-6 text-blue-600" />
          </div>
          <div className="mt-5 space-y-3">
            {[
              [CircleDollarSign, "المؤشرات المالية", "راجع الإيرادات والمصروفات من التقارير المالية."],
              [Users, "المستخدمون والصلاحيات", "راجع الأدوار والوصول عند إضافة أعضاء جدد."],
              [CheckCircle2, "الموافقات", "تابع العمليات التي تحتاج اعتمادًا قبل الترحيل."],
            ].map(([Icon, title, description]) => (
              <div key={String(title)} className="flex gap-3 rounded-2xl bg-slate-50 p-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-700"><Icon className="h-5 w-5" /></span>
                <div><b className="block text-sm">{String(title)}</b><p className="mt-1 text-xs leading-5 text-slate-500">{String(description)}</p></div>
              </div>
            ))}
          </div>
          <Link to="/helpdesk" className="mt-5 inline-flex text-sm font-bold text-blue-600 hover:text-blue-700">فتح Prime AI Help Desk →</Link>
        </div>
      </section>

      <RecentActivities />
    </div>
  );
}
