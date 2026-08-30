import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import type { DashboardStatistic } from "../../types/dashboard.types";

interface StatisticCardProps {
  statistic: DashboardStatistic;
}

export default function StatisticCard({
  statistic,
}: StatisticCardProps) {
  const Icon = statistic.icon;
  const isPositive = statistic.change >= 0;

  return (
    <article className="rounded-2xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            {statistic.title}
          </p>

          <p className="mt-3 text-2xl font-bold tracking-tight">
            {statistic.value}
          </p>
        </div>

        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-5 flex items-center gap-2 text-xs">
        <span
          className={[
            "inline-flex items-center gap-1 rounded-full px-2 py-1 font-semibold",
            isPositive
              ? "bg-emerald-500/10 text-emerald-600"
              : "bg-red-500/10 text-red-600",
          ].join(" ")}
        >
          {isPositive ? (
            <ArrowUpRight className="h-3.5 w-3.5" />
          ) : (
            <ArrowDownRight className="h-3.5 w-3.5" />
          )}

          {Math.abs(statistic.change)}%
        </span>

        <span className="text-muted-foreground">
          {statistic.changeLabel}
        </span>
      </div>
    </article>
  );
}
