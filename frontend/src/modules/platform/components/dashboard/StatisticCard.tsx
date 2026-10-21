import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { DashboardStatistic } from "../../types/dashboard.types";

interface StatisticCardProps { statistic: DashboardStatistic; }

export default function StatisticCard({ statistic }: StatisticCardProps) {
  const Icon = statistic.icon;
  const positive = statistic.change >= 0;
  return <article className="group relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-slate-900/5">
    <div className="absolute -left-10 -top-10 size-28 rounded-full bg-blue-50 opacity-0 transition group-hover:opacity-100"/>
    <div className="relative flex items-start justify-between gap-4"><div><p className="text-sm font-semibold text-slate-500">{statistic.title}</p><p className="mt-3 text-3xl font-black tracking-tight text-slate-950">{statistic.value}</p></div><div className="flex size-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 transition group-hover:bg-blue-600 group-hover:text-white"><Icon className="size-5"/></div></div>
    <div className="relative mt-5 flex items-center gap-2 text-xs"><span className={"inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-black " + (positive ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700")}>{positive ? <ArrowUpRight className="size-3.5"/> : <ArrowDownRight className="size-3.5"/>}{Math.abs(statistic.change)}%</span><span className="text-slate-400">{statistic.changeLabel}</span></div>
  </article>;
}
